export const localStorageEffect = (key, options?: { session?: boolean }) => ({
  setSelf,
  onSet,
}) => {
  const storage = options?.session ? sessionStorage : localStorage;

  const savedValue = storage.getItem(key);

  if (savedValue != null) {
    setSelf(JSON.parse(savedValue));
  }

  onSet((newValue) => {
    storage.setItem(key, JSON.stringify(newValue));
  });
};
