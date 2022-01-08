import React from 'react';

declare global {
  export type GetComponentProps<T> = T extends
    | React.ComponentType<infer P>
    | React.ElementType<infer P>
    ? P
    : never;

  export type ValueOf<T> = T[keyof T];

  // Flatten an intersection type by merging keys:
  export type Flatten<T> = T extends Record<string, any>
    ? { [k in keyof T]: T[k] }
    : never;

  export type DiscriminateUnion<
    T,
    K extends keyof T,
    V extends T[K]
  > = T extends Record<K, V> ? T : never;

  export type RecordValueMap<T, V> = {
    [P in keyof T]: V;
  };

  export type RecordFromUnion<
    T extends Record<K, string>,
    K extends keyof T
  > = {
    [V in T[K]]: DiscriminateUnion<T, K, V>;
  };

  export type RecordFromUnionWithPick<
    T extends Record<K, string>,
    K extends keyof T,
    P extends keyof T
  > = {
    [V in T[K]]: Pick<DiscriminateUnion<T, K, V>, P>;
  };

  export type RecordFromUnionWithOmit<
    T extends Record<K, string>,
    K extends keyof T,
    P extends keyof T
  > = {
    [V in T[K]]: Omit<DiscriminateUnion<T, K, V>, P>;
  };

  // A better Omit
  export type DistributiveOmit<T, K extends keyof any> = T extends any
    ? Omit<T, K>
    : never;

  export type PartialExcept<T, K extends keyof T> = Pick<T, K> & Partial<T>;

  export type RecursivePartial<T> = {
    [P in keyof T]?: T[P] extends (infer U)[]
      ? RecursivePartial<U>[]
      : T[P] extends object
      ? RecursivePartial<T[P]>
      : T[P];
  };

  export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<T>;

  export type Replace<
    T,
    P extends keyof T,
    R extends Partial<Record<keyof T, any>>
  > = Omit<T, P> & R;
}
