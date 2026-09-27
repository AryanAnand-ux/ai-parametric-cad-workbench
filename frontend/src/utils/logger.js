/**
 * logger.js — Dev-only logging utility.
 *
 * All methods are gated on `import.meta.env.DEV`, so they are completely
 * silent in production builds. Use `logger.warn` / `logger.error` /
 * `logger.info` instead of raw `console.*` calls in app code.
 */

const isDev = import.meta.env.DEV;

export const logger = {
  warn(...args) {
    if (isDev) console.warn(...args);
  },
  error(...args) {
    if (isDev) console.error(...args);
  },
  info(...args) {
    if (isDev) console.info(...args);
  },
};

export default logger;
