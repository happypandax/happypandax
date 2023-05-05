import { createImageHandler } from './index';

export default createImageHandler('thumb');

export const config = {
  api: {
    responseLimit: false,
  },
};
