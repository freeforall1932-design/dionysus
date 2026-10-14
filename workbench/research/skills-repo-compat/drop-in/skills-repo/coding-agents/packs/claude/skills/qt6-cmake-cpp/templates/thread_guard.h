// thread_guard.h — thread-affinity assertion for QObject methods.
//
// Usage:
//   void Worker::process() {
//       ASSERT_THREAD(this);          // logs class/method/threads, then Q_ASSERT_X
//       ...
//   }
//
// Why: a QObject touched from a thread other than the one it lives on is the
// classic "random crash three minutes later". Qt only warns for some cases
// (and only if the object is a QWidget or uses timers). This makes every
// guarded method fail loudly, at the call site, in debug builds, and log in
// release builds (Q_ASSERT_X compiles out with QT_NO_DEBUG).
//
// Header-only; depends on Qt Core. Written fresh for this skill (2026-10-13);
// not compiled in the authoring sandbox — build it with the first project.

#pragma once

#include <QLoggingCategory>
#include <QObject>
#include <QThread>

Q_DECLARE_LOGGING_CATEGORY(lcThreadGuard)

#ifndef APP_THREAD_GUARD_CATEGORY_DEFINED
// Define the category once in exactly one translation unit by compiling with
// -DAPP_THREAD_GUARD_DEFINE_CATEGORY, or copy the line below into a .cpp.
#  ifdef APP_THREAD_GUARD_DEFINE_CATEGORY
Q_LOGGING_CATEGORY(lcThreadGuard, "core.thread")
#  endif
#endif

namespace app {

class ThreadGuard {
 public:
  ThreadGuard(const QObject* obj, const char* method) noexcept {
    if (!obj) return;
    QThread* owner = obj->thread();
    QThread* current = QThread::currentThread();
    if (owner == current) return;
    qCCritical(lcThreadGuard).noquote()
        << "THREAD VIOLATION:" << obj->metaObject()->className()
        << "name=" << obj->objectName()
        << "method=" << method
        << "called_on=" << current << "owner=" << owner;
    Q_ASSERT_X(false, method, "method called from a thread other than the object's owner thread");
  }
};

// Log every thread transfer; forbid moving an object you are not currently on.
template <typename T>
inline void safeMoveToThread(T* obj, QThread* target) {
  Q_ASSERT_X(QThread::currentThread() == obj->thread(), "safeMoveToThread",
             "moveToThread must be called from the object's current thread");
  qCInfo(lcThreadGuard).noquote()
      << "Thread transfer:" << obj->metaObject()->className()
      << "name=" << obj->objectName()
      << "from=" << obj->thread() << "to=" << target;
  // ql-allow QL005: this helper only performs the transfer; the caller's connects choose Qt::QueuedConnection
  obj->moveToThread(target);
}

}  // namespace app

#define ASSERT_THREAD(obj) ::app::ThreadGuard _app_thread_guard_((obj), Q_FUNC_INFO)
