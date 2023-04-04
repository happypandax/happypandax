import { GlobalState } from '../../state/global';
import { logout as logoutQuery } from '../queries';

export class GeneralActions {
  static logout() {
    return logoutQuery().then((r) => {
      GlobalState.setState({
        loggedIn: false,
        user: null,
      });
      return r;
    });
  }
}
