// offscreen_test_main.cpp — house-style offscreen GUI harness skeleton.
//
// Runs the REAL main window under QT_QPA_PLATFORM=offscreen, drives it by
// objectName, auto-closes modal dialogs (recording them), counts CHECKs, and
// exits non-zero on any failure. No test framework dependency; swap in Qt Test
// if the project prefers it — but not both.
//
// Conventions this skeleton encodes (references/testing.md):
//   * every block prints its id + purpose; the summary prints counts from THIS run
//   * widgets are found by objectName — a public test API
//   * waits are bounded (deadline), never unbounded spins
//   * fixtures come from an env var (APP_TEST_FIXTURES) with a clear failure if unset
//   * a crash prints no FAIL line — the CI step must check the exit status
//
// Written fresh for this skill (2026-10-13); not compiled in the authoring
// sandbox — adapt MainWindow/object names to the project and build it there.

#include <QApplication>
#include <QDialog>
#include <QElapsedTimer>
#include <QLabel>
#include <QPushButton>
#include <QTimer>
#include <QWidget>

#include <cstdio>
#include <cstdlib>
#include <functional>

// #include "ui/MainWindow.h"   // the project's real window

namespace {

int g_blocks = 0;
int g_checks = 0;
int g_fails = 0;

#define CHECK(expr)                                                        \
  do {                                                                     \
    ++g_checks;                                                            \
    if (!(expr)) {                                                         \
      ++g_fails;                                                           \
      std::fprintf(stderr, "FAIL %s:%d  %s\n", __FILE__, __LINE__, #expr); \
    }                                                                      \
  } while (0)

#define CHECK_EQ(a, b)                                                               \
  do {                                                                               \
    ++g_checks;                                                                      \
    if (!((a) == (b))) {                                                             \
      ++g_fails;                                                                     \
      std::fprintf(stderr, "FAIL %s:%d  %s == %s\n", __FILE__, __LINE__, #a, #b);    \
    }                                                                                \
  } while (0)

void block(const char* id, const char* purpose) {
  ++g_blocks;
  std::fprintf(stderr, "== %s  %s\n", id, purpose);
}

// Pump the event loop until pred() is true or the deadline passes. Returns pred().
bool waitUntil(const std::function<bool()>& pred, int deadlineMs = 5000) {
  QElapsedTimer t;
  t.start();
  while (!pred() && t.elapsed() < deadlineMs) {
    // ql-allow QL004: a harness pumps the loop on purpose; product code must not (testing.md)
    QApplication::processEvents(QEventLoop::AllEvents, 50);
  }
  return pred();
}

// Find a child by objectName or fail loudly (returns nullptr after a FAIL line).
template <typename T>
T* find(QWidget* root, const char* name) {
  T* w = root->findChild<T*>(QString::fromLatin1(name));
  ++g_checks;
  if (!w) {
    ++g_fails;
    std::fprintf(stderr, "FAIL missing widget objectName=%s\n", name);
  }
  return w;
}

// Records and closes every visible QDialog. Titles/texts are an assertion surface.
class DialogKiller : public QObject {
 public:
  QStringList seen;
  explicit DialogKiller(QObject* parent = nullptr) : QObject(parent) {
    auto* t = new QTimer(this);
    connect(t, &QTimer::timeout, this, [this] { sweep(); });
    t->start(50);
  }
  void sweep() {
    const auto tops = QApplication::topLevelWidgets();
    for (QWidget* w : tops) {
      auto* d = qobject_cast<QDialog*>(w);
      if (d && d->isVisible()) {
        seen << QStringLiteral("%1 | %2").arg(d->windowTitle(), summarize(d));
        d->reject();
      }
    }
  }
  static QString summarize(QDialog* d) {
    const auto labels = d->findChildren<QLabel*>();
    QString s;
    for (QLabel* l : labels) {
      if (!l->text().isEmpty()) { s = l->text().left(120); break; }
    }
    return s;
  }
};

}  // namespace

int main(int argc, char* argv[]) {
  if (qEnvironmentVariableIsEmpty("QT_QPA_PLATFORM")) qputenv("QT_QPA_PLATFORM", "offscreen");
  QApplication app(argc, argv);

  const QString fixtures = qEnvironmentVariable("APP_TEST_FIXTURES");
  if (fixtures.isEmpty()) {
    std::fprintf(stderr, "FAIL APP_TEST_FIXTURES is not set (directory with decoded fixtures)\n");
    return 2;
  }

  DialogKiller killer;

  // MainWindow w;  w.show();  QApplication::processEvents();
  QWidget w;  // placeholder so the skeleton is self-contained
  w.setObjectName(QStringLiteral("mainWindow"));
  auto* run = new QPushButton(&w);
  run->setObjectName(QStringLiteral("runButton"));
  w.show();

  block("T1", "defaults: primary action present and enabled, no dialog on start");
  {
    QPushButton* b = find<QPushButton>(&w, "runButton");
    CHECK(b && b->isEnabled());
    CHECK(waitUntil([&] { return true; }, 100));
    CHECK_EQ(killer.seen.size(), 0);
  }

  // block("T2", "run against fake_engine_ok: status becomes Complete only after output verified");
  // block("T3", "fake_engine_fail: previous output intact, status Failed, exactly one dialog");
  // block("T4", "cancel mid-run against a sleeping engine: Cancelled, temp removed, original kept");

  std::fprintf(stderr, "== SUMMARY %d blocks, %d checks, %d failures\n", g_blocks, g_checks, g_fails);
  return g_fails == 0 ? 0 : 1;
}
