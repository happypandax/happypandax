/* eslint-disable global-require */
/* eslint-disable no-console */
import {
  createConsoleProcessor,
  createDateAndLevelPrependProcessor,
  createStackTraceTransformProcessor,
  createThrottleProcessor,
  Logger,
  LogLevel,
  Processor,
  Record,
} from '@grabrinc/isomorphic-logger';

function createObjectTransformProcessor(): Processor {
  return (
    records: Record[]
  ): Promise<Record[]> | Record[] | Promise<null> | null => {
    return records.map((v, i) => ({
      ...v,
      messages: v.messages.map((m, i) =>
        typeof m === 'object' && typeof window === 'undefined'
          ? require('util').inspect(m, false, null, true)
          : m
      ),
    }));
  };
}

export default function setupLogger({
  level
}: {
  level?: LogLevel;
} = {}) {
  const logger = new Logger();
  // eslint-disable-next-line no-restricted-syntax
  for (const k of Object.keys(Logger.prototype)) {
    logger[k] = logger[k].bind(logger);
  }

  logger.channel(
    ...[
      createStackTraceTransformProcessor(), // Converts error objects to string representing stack trace.
      createDateAndLevelPrependProcessor(), // Prepends every message with date and time.
      process.env.NODE_ENV !== 'test'
        ? createThrottleProcessor({ delay: 100, length: 10 })
        : undefined, // Batch logged messages.
      createObjectTransformProcessor(),
      createConsoleProcessor(), // Write batched messages to console.
    ].filter(Boolean)
  );

  logger.setLevel(
    level ?? (process.env.NODE_ENV !== 'production' ? LogLevel.DEBUG : LogLevel.INFO)
  );

  function log(...args: any[]) {
    logger.info(...args);
  }
  // eslint-disable-next-line no-underscore-dangle
  log._logger = logger;
  log.i = logger.info.bind(logger);
  log.w = logger.warn.bind(logger);
  log.e = logger.error.bind(logger);
  log.c = logger.error.bind(logger);
  log.d = logger.debug.bind(logger);

  return log as {
    (...args: any[]): void;
    i: (...args: any[]) => void;
    w: (...args: any[]) => void;
    e: (...args: any[]) => void;
    c: (...args: any[]) => void;
    d: (...args: any[]) => void;
  };
}

export type Logger = ReturnType<typeof setupLogger>;
