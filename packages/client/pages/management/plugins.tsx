import { useCallback } from 'react';
import { Container, Form, Segment } from 'semantic-ui-react';

import { useConfig } from '../../client/hooks/settings';
import t from '../../client/lang';
import { PageTitle } from '../../components/misc';
import { Plugins } from '../../components/Plugin';
import { IsolationLabel, OptionField } from '../../components/Settings';
import ManagementPage from './';

interface PageProps {}

export default function Page({}: PageProps) {
  const [cfg, setConfig] = useConfig({
    'plugin.dev': undefined as boolean,
    'plugin.auto_install_plugin_dependency': undefined as boolean,
    'plugin.plugin_dir': undefined as string,
    'plugin.check_plugin_release_interval': undefined as number,
    'plugin.auto_install_plugin_release': undefined as boolean,
    'plugin.check_new_plugin_releases': undefined as boolean,
  });

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  return (
    <ManagementPage>
      <PageTitle title={t`Plugins`} />
      <Container centered clearing as={Segment} basic>
        <Form>
          <Segment clearing>
            <IsolationLabel attached="top left" isolation="server" />
            <OptionField
              label={t`Additional plugin directory to look for plugins`}
              cfg={cfg}
              nskey="plugin.plugin_dir"
              type="string"
              optionChange={optionChange}
            />
            <OptionField
              label={t`Automatically install a plugin's dependencies when installing a plugin`}
              cfg={cfg}
              nskey="plugin.auto_install_plugin_dependency"
              type="boolean"
              optionChange={optionChange}
            />
            <OptionField
              label={t`Regularly check plugins for updates`}
              cfg={cfg}
              nskey="plugin.check_new_plugin_releases"
              type="boolean"
              optionChange={optionChange}
            />
            <OptionField
              label={t`Interval in minutes between checking for a new plugin update, set 0 to only check once every startup`}
              cfg={cfg}
              nskey="plugin.check_plugin_release_interval"
              type="number"
              inputLabel={t`minutes`}
              optionChange={optionChange}
            />
            <OptionField
              label={t`Automatically download and install new plugin updates`}
              cfg={cfg}
              nskey="plugin.auto_install_plugin_release"
              type="boolean"
              optionChange={optionChange}
            />
            <OptionField
              label={t`Enable plugin development mode`}
              cfg={cfg}
              nskey="plugin.dev"
              type="boolean"
              optionChange={optionChange}
            />
          </Segment>
        </Form>

        <Plugins defaultVisibleInactive />
      </Container>
    </ManagementPage>
  );
}
