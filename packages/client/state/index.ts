import useEffect, { useState } from 'react';
import { useEffectOnce, useUpdateEffect } from 'react-use';
import { RecoilState, SetterOrUpdater, useRecoilState } from 'recoil';

import { AppState } from './_app';
import StateBlock from './_base';
import { DataState } from './_data';
import { LibraryState } from './_library';

((...cls: StateBlock[]) => {
  cls.forEach((c) => StateBlock.setup(c));
})(AppState, LibraryState, DataState);

export function useInitialRecoilState<T>(
  state: RecoilState<T>,
  optional?: T
): [T, SetterOrUpdater<T>] {
  const [value, setValue] = useRecoilState(state);
  const [optionalValue, setOptionalValue] = useState([value, optional]);

  useEffectOnce(() => {
    if (optional === value) {
      setOptionalValue(undefined);
    } else {
      setValue(optional);
    }
  });

  useUpdateEffect(() => {
    setOptionalValue(undefined);
  }, [value]);

  return [
    optionalValue === undefined || value !== optionalValue[0]
      ? value
      : optionalValue[1],
    setValue,
  ];
}

export function useInitialRecoilValue<T>(state: RecoilState<T>, optional?: T) {
  const [value, setValue] = useRecoilState(state);
  const [optionalValue, setOptionalValue] = useState([value, optional]);

  useEffectOnce(() => {
    if (optional === value) {
      setOptionalValue(undefined);
    } else {
      setValue(optional);
    }
  });

  useUpdateEffect(() => {
    setOptionalValue(undefined);
  }, [value]);

  return optionalValue === undefined || value !== optionalValue[0]
    ? value
    : optionalValue[1];
}

export { AppState, LibraryState, DataState };
