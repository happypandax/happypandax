import { createImageHandler } from './index';

// THIS IS SPECIFIC TO WHEN THE WEBSERVER IS STARTED BY HPX SERVER

export default createImageHandler('page');

export const config = {
  api: {
    responseLimit: false,
  },
};
