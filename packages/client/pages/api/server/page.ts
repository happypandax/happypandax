import { createImageHandler } from './index';

export default createImageHandler('page');

export const config = {
  api: {
    responseLimit: false,
  },
};
