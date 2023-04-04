import classNames from 'classnames';
import { useRouter } from 'next/dist/client/router';
import { useCallback, useState } from 'react';
import {
  Button,
  Checkbox,
  Divider,
  Grid,
  Header,
  Segment,
  Step,
} from 'semantic-ui-react';

import t from '../client/lang';
import { Markdown } from './misc';

function StepBody({
  show,
  noNext,
  onNext,
  children,
  title,
}: {
  children?: React.ReactNode;
  show?: boolean;
  onNext: () => void;
  noNext?: boolean;
  title: React.ReactNode;
}) {
  if (!show) return null;

  return (
    <>
      <Grid.Row>
        <Grid.Column>
          <Header
            as="h2"
            disabled={!show}
            className={classNames('center-text')}
          >
            {title}
          </Header>
          {children}
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          {!noNext && (
            <div className="center-text">
              <Button onClick={onNext} primary>{t`Next`}</Button>
            </div>
          )}
        </Grid.Column>
      </Grid.Row>
    </>
  );
}

function BackendStep(props: any) {
  const [backend, setBackend] = useState('sqlite');

  return (
    <StepBody {...props}>
      <Markdown>
        {t`The following database backends are supported:

- SQLite
- PostgreSQL

Before using HPX, it is important that you settle on a backend because transferring data between backends might prove problematic.
If you’re not sure which one you should pick, go with PostgreSQL. SQLite doesn’t handle large databases and concurrency that well.
PostgreSQL will therefor be the faster and more stable choice but it requires a bit of setup before you can use it.
Setting up a server based database like PostgreSQL differs for each platform.
There should be plenty of [guides on google](https://lmgtfy.app/?q=how+to+install+postgresql+on+platform) to help you.

Some things that can help you choose:

- Going with SQLite is a bad idea if you're going to have more than 500-1000 galleries.
- If you're going to have multiple people use your HPX instance simultaneously, absolutely go with PostgresSQL.
- Just go with PostgresSQL already, you baka!
`}
      </Markdown>
      <div className="center-text medium-margin">
        <Button.Group>
          <Button
            active={backend === 'sqlite'}
            color={backend === 'sqlite' ? 'green' : undefined}
            onClick={useCallback(() => setBackend('sqlite'), [])}
          >
            SQLite
          </Button>
          <Button.Or />
          <Button
            active={backend === 'postgresql'}
            color={backend === 'postgresql' ? 'green' : undefined}
            onClick={useCallback(() => setBackend('postgresql'), [])}
          >
            PostgreSQL
          </Button>
        </Button.Group>
      </div>
    </StepBody>
  );
}

function UsersStep(props: any) {
  const [defaultEnabled, setDefaultEnabled] = useState(true);
  const [guestsEnabled, setGuestsEnabled] = useState(true);
  const [requireAuth, setRequireAuth] = useState(false);

  return (
    <StepBody {...props}>
      <Markdown>
        {`A single admin super-usercalled \`default\` is created with no password. This user is enabled by default.
If you’re planning on having multiple people accessing your HPX instance, or you want to access the server from a remote origin over the internet,
it is advised that you disable this user.
`}
      </Markdown>
      <div className="center-text medium-margin">
        <Checkbox
          label={t`Enable default user`}
          checked={defaultEnabled}
          onChange={useCallback((v) => setDefaultEnabled(v.checked), [])}
          toggle
        />
      </div>
      <Markdown>
        {`Additionally, you may also want to disallow people accessing the server without logging.`}
      </Markdown>
      <div className="center-text medium-margin">
        <Checkbox
          label={t`Enable guests`}
          checked={guestsEnabled}
          onChange={useCallback((v) => setGuestsEnabled(v.checked), [])}
          toggle
        />
      </div>
      <div className="center-text medium-margin">
        <Checkbox
          label={t`Require authentication`}
          checked={requireAuth}
          onChange={useCallback((v) => setRequireAuth(v.checked), [])}
          toggle
        />
      </div>
      <Markdown>
        {`To create and delete users, see the command-line argument \`user --help\` or use the GUI.`}
      </Markdown>
    </StepBody>
  );
}

function PluginStep(props: any) {
  const [defaultEnabled, setDefaultEnabled] = useState(true);
  const [guestsEnabled, setGuestsEnabled] = useState(true);
  const [requireAuth, setRequireAuth] = useState(false);

  return (
    <StepBody {...props}>
      <Markdown>
        {`Your HPX instance can be extended with plugins. If you wish to create a plugin for HPX then head over to [Plugins](https://happypandax.github.io/plugin.html#plugins).

HPX looks for plugins in the following folders:

  - \`[HPX]/plugins\` which exists in your HPX root folder

  - a folder defined by the \`plugin.plugin_dir\` setting

If you’re on OS X, your root HPX folder is inside the bundle at \`HappyPanda X.app/Contents/MacOS/\` which might be a bit bothersome
so I recommend that you define a new folder of your choosing where HPX can look for plugins in with the \`plugin.plugin_dir setting\`.

Each plugin is contained in its own folder.
To register a plugin with HPX, just move the plugin’s folder into one of the locations above.
HPX will then discover and register it, **but not install it**.

To automatically install plugins once discovered and registered, set the setting \`plugin.auto_install_plugin\` to \`true\`, but this is not recommended for the reasons explained below.

A plugin may depend on other plugins that needs to be installed first before it can be installed.
There’s the setting \`plugin.auto_install_plugin_dependency\` which is set to \`true\` by default that controls if these plugin dependencies should be installed automatically when the plugin in question is being installed.

### Be careful about plugins

**A plugin can not do anything before it has been installed.**

If you give HPX elevated privileges when running, plugins will also have this privilege **but not before they have been installed**.
Know that inherently, **HappyPanda X does not need elevated privileges** to function.

Some plugins may also cause unwanted effects towards your system or database. That is why care should be taken when wanting to use a plugin.
Only use those you trust, and also don’t just blindly trust a plugin. Backing up your HPX database before installing a plugin is recommended.

This all sounds scary and you might even question why even use plugins. HPX tries its best to minimize some of these issues.
As long as plugin developers follow the guidelines and write safe code then everything should be okay.

The [HappyPanda X Plugin Repo](https://github.com/happypandax/plugins) houses plugins that have been checked and are pretty safe to use.
If you’re a plugin developer and want your plugin in there, just submit a PR.
`}
      </Markdown>
    </StepBody>
  );
}

export default function Setup() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { title: `Choose a backend`, content: BackendStep },
    { title: `Manage users`, content: UsersStep },
    { title: `Install plugins`, content: PluginStep },
    { title: `Import galleries`, content: StepBody },
    { title: `Fetch metadata`, content: StepBody },
    {
      title: `Done!`,
      content: useCallback(
        (props: any) => (
          <StepBody
            {...props}
            title={t`and a parting word from Momo-chan...`}
            noNext
          >
            <div className="center-text">
              <img src="/img/masturbated.png" height={500} />
            </div>
            <div className="center-text">
              <Button size="large" color="green">{t`I feel honored!`}</Button>
            </div>
          </StepBody>
        ),
        []
      ),
    },
  ];

  return (
    <Grid
      className="min-fullheight animate__animated animate__fadeInUp"
      centered
      verticalAlign="middle"
      as={Segment}
    >
      <Grid.Row>
        <Grid.Column>
          <div className="center-text">
            <img src="/img/hpx_logo.svg" className="hpxlogo" alt="hpxlogo" />
          </div>
          <Divider hidden horizontal />
          <Header as="h1" className="center-text">
            {t`Momo-chan will help you set up HPX...`}
          </Header>
          <div className="auto-margin center-text">
            <Step.Group size="tiny">
              {steps.map((s, i) => (
                <Step
                  key={s.title}
                  active={currentStep === i}
                  id={`step-${i}`}
                  link
                  onClick={() => setCurrentStep(i)}
                >
                  <Step.Content>
                    <Step.Title>{s.title}</Step.Title>
                  </Step.Content>
                </Step>
              ))}
            </Step.Group>
          </div>
        </Grid.Column>
      </Grid.Row>
      {steps.map((v, i) => {
        const El = v.content;

        return (
          <El
            key={v.title}
            title={v.title}
            show={currentStep === i}
            onNext={() => {
              setCurrentStep(i + 1);
              router.push({ search: `step-${i}` });
            }}
          />
        );
      })}
    </Grid>
  );
}
