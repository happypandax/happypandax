import { atom } from 'recoil';

import StateBlock from './base';

export default class AppState extends StateBlock {
  static test = atom({
    key: 'test',
    default: true,
  });
}
