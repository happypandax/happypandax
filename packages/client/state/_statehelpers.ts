export const localStorageEffect = (key, session = false) => ({
  setSelf,
  onSet,
}) => {
  const storage = session ? sessionStorage : localStorage;

  const savedValue = storage.getItem(key);

  if (savedValue != null) {
    setSelf(JSON.parse(savedValue));
  }

  onSet((newValue) => {
    storage.setItem(key, JSON.stringify(newValue));
  });
};
