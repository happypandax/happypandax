import { Cache, schema } from 'normalized-cache';

const Gallery = schema.object({
  name: 'Gallery',
});

export function createCache() {
  const cache = new Cache({
    types: [Gallery],
  });

  return cache;
}
