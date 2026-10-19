// logging.h — per-module logging categories, a one-line structured message
// handler, and a bounded ring buffer for crash records.
//
// Format (one line, greppable, no multi-line messages):
//   2026-10-13T20:41:07.123Z tid=0x7f3a core.process INFO  engine started pid=4242 argv=[...]
//
// Install in main() right after QApplication:
//   app::Logging::install(QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/app.log");
// Then declare categories per MODULE (not per class) in one .cpp:
//   Q_LOGGING_CATEGORY(lcCoreProcess, "core.process")
//   Q_LOGGING_CATEGORY(lcUiMain,      "ui.main")
// and use qCInfo(lcCoreProcess) << ...;
//
// Run-time control without a rebuild: QT_LOGGING_RULES="core.process.debug=true".
// Crash record: app::Logging::tail(500) returns the last lines for a companion
// text file (see references/crash-diagnosis.md §5).
//
// Header-only; depends on Qt Core. Written fresh for this skill (2026-10-13);
// not compiled in the authoring sandbox — build it with the first project.

#pragma once

#include <QDateTime>
#include <QFile>
#include <QMutex>
#include <QMutexLocker>
#include <QString>
#include <QStringList>
#include <QTextStream>
#include <QThread>
#include <QtGlobal>

#include <cstdio>
#include <vector>

namespace app {

class Logging {
 public:
  // Install the handler. logPath may be empty (stderr + ring buffer only).
  static void install(const QString& logPath = QString(), int ringCapacity = 1000) {
    Logging& L = self();
    QMutexLocker lock(&L.mutex_);
    L.ring_.assign(static_cast<size_t>(ringCapacity), QString());
    L.head_ = 0;
    L.count_ = 0;
    if (!logPath.isEmpty()) {
      L.file_.setFileName(logPath);
      if (!L.file_.open(QIODevice::Append | QIODevice::Text)) {
        std::fprintf(stderr, "logging: cannot open %s\n", qPrintable(logPath));
      }
    }
    L.previous_ = qInstallMessageHandler(&Logging::handler);
  }

  static void flush() {
    Logging& L = self();
    QMutexLocker lock(&L.mutex_);
    if (L.file_.isOpen()) L.file_.flush();
    std::fflush(stderr);
  }

  // Last n lines, oldest first. Safe to call from a crash handler only in the
  // sense that it takes the mutex; if the crash happened while logging, this
  // may block — call it from a watchdog thread or accept the risk.
  static QStringList tail(int n = 500) {
    Logging& L = self();
    QMutexLocker lock(&L.mutex_);
    QStringList out;
    const int cap = static_cast<int>(L.ring_.size());
    const int have = qMin(n, L.count_);
    for (int i = have; i > 0; --i) {
      int idx = (L.head_ - i + cap) % cap;
      out << L.ring_[static_cast<size_t>(idx)];
    }
    return out;
  }

 private:
  Logging() = default;
  static Logging& self() {
    static Logging instance;
    return instance;
  }

  static const char* level(QtMsgType t) {
    switch (t) {
      case QtDebugMsg:    return "DEBUG";
      case QtInfoMsg:     return "INFO ";
      case QtWarningMsg:  return "WARN ";
      case QtCriticalMsg: return "CRIT ";
      case QtFatalMsg:    return "FATAL";
    }
    return "?????";
  }

  static void handler(QtMsgType type, const QMessageLogContext& ctx, const QString& msg) {
    const QString line = QStringLiteral("%1 tid=0x%2 %3 %4 %5")
        .arg(QDateTime::currentDateTimeUtc().toString(Qt::ISODateWithMs))
        .arg(reinterpret_cast<quintptr>(QThread::currentThreadId()), 0, 16)
        .arg(QString::fromLatin1(ctx.category ? ctx.category : "default"))
        .arg(QString::fromLatin1(level(type)))
        .arg(QString(msg).replace(QLatin1Char('\n'), QStringLiteral("\\n")));

    Logging& L = self();
    {
      QMutexLocker lock(&L.mutex_);
      if (!L.ring_.empty()) {
        L.ring_[static_cast<size_t>(L.head_)] = line;
        L.head_ = (L.head_ + 1) % static_cast<int>(L.ring_.size());
        L.count_ = qMin(L.count_ + 1, static_cast<int>(L.ring_.size()));
      }
      if (L.file_.isOpen()) {
        QTextStream ts(&L.file_);
        ts << line << '\n';
        if (type >= QtWarningMsg) ts.flush();
      }
    }
    std::fprintf(stderr, "%s\n", qPrintable(line));

    if (type == QtFatalMsg) {
      // Write the crash record BEFORE Qt aborts. Hook your companion-file writer here.
      flush();
    }
    // Do not chain to the previous handler for fatal messages: Qt's default
    // aborts, and we want our flush to have happened first (it has, above).
  }

  QMutex mutex_;
  std::vector<QString> ring_;
  int head_ = 0;
  int count_ = 0;
  QFile file_;
  QtMessageHandler previous_ = nullptr;
};

}  // namespace app
