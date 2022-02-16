import { useCallback, useEffect, useState } from 'react';

import { update } from '../../misc/utility';
import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../queries';

export function useConfig<T extends Record<string, any> = Record<string, any>>(
  cfg?: T
): [Partial<T>, (cfg: Partial<T>) => void] {
  const [value, setValue] = useState<Partial<T>>(cfg ?? {});

  const { data, remove } = useQueryType(QueryType.CONFIG, {
    cfg: cfg ?? {},
    flatten: true,
  });

  const { mutate } = useMutationType(MutatationType.UPDATE_CONFIG);

  useEffect(() => {
    if (data?.data) {
      setValue(data.data as T);
    }
  }, [data]);

  const setConfig = useCallback(
    (cfg: Partial<T>) => {
      setValue(update(value, { $merge: cfg }));

      mutate(
        { cfg },
        {
          onSuccess: () => {
            remove();
          },
          onError: (error) => {
            console.error(error);
            // reverts
            setValue(value);
          },
        }
      );
    },
    [value]
  );

  return [value, setConfig];
}

export function useSetting<T = any>(
  key: string,
  defaultValue?: T
): [T, (value: T) => void] {
  const [config, setConfig] = useConfig(
    defaultValue !== undefined ? { [key]: defaultValue } : undefined
  );

  const setValue = useCallback(
    (value: any) => {
      setConfig({
        [key]: value,
      });
    },
    [setConfig]
  );

  return [config[key], setValue];
}
