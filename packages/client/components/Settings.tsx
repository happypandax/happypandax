import classNames from 'classnames';
import { useCallback, useMemo } from 'react';
import { useRecoilState } from 'recoil';
import {
  Checkbox,
  Form,
  FormFieldProps,
  Header,
  Icon,
  Input,
  Label,
  Modal,
  Segment,
  Select,
  Tab,
} from 'semantic-ui-react';

import { useConfig } from '../client/hooks/settings';
import t from '../misc/lang';
import { defined } from '../misc/utility';
import { AppState } from '../state';

function namespaceExists(
  cfg: Record<string, any>,
  ns: string,
  keys: string[] = []
) {
  return (
    Object.keys(cfg).some((key) => key.startsWith(ns)) &&
    (!keys.length || keys.some((key) => defined(cfg[key])))
  );
}

function IsolationLabel({ isolation }: { isolation: 'user' | 'client' }) {
  return (
    <Label
      horizontal
      size="mini"
      title={
        isolation === 'user'
          ? t`This option is isolated to the user`
          : t`This option is isolated to the client`
      }
      color={isolation === 'user' ? 'purple' : 'teal'}>
      {isolation === 'user' ? t`User` : t`Client`}
    </Label>
  );
}

function OptionField<
  T extends Record<string, any>,
  K extends keyof T,
  I extends 'select' | 'number' | 'boolean' | 'string'
>({
  nskey,
  label,
  type,
  cfg,
  float,
  help,
  optionChange,
  isolation,
  width,
  visible,
  children,
  ...rest
}: {
  cfg: T;
  label: string;
  help?: string;
  float?: boolean;
  width?: FormFieldProps['width'];
  isolation?: 'user' | 'client';
  visible?: boolean;
  nskey: K;
  children?: React.ReactNode;
  optionChange: (key: K, value: T[K]) => void;
  type: I;
} & Omit<
  I extends 'select'
    ? React.ComponentProps<typeof Select>
    : I extends 'boolean'
    ? React.ComponentProps<typeof Checkbox>
    : I extends 'number'
    ? React.ComponentProps<typeof Input>
    : I extends 'string'
    ? React.ComponentProps<typeof Input>
    : never,
  'value' | 'label' | 'type'
>) {
  return defined(cfg[nskey]) || visible ? (
    <>
      <Form.Field width={width}>
        {type !== 'boolean' && (
          <label>
            {isolation && <IsolationLabel isolation={isolation} />}
            {label}
          </label>
        )}
        {type === 'boolean' && (
          <Checkbox
            toggle
            label={
              <>
                {isolation && <IsolationLabel isolation={isolation} />}
                <label>{label}</label>
              </>
            }
            checked={cfg[nskey] as any}
            onChange={(ev, { checked }) => {
              ev.preventDefault();
              optionChange(nskey, checked as any);
            }}
            {...rest}
          />
        )}
        {type === 'select' && (
          <Select
            options={rest.options}
            value={cfg[nskey]}
            onChange={(ev, { value }) => {
              ev.preventDefault();
              optionChange(nskey, value as any);
            }}
            {...rest}
          />
        )}
        {(type === 'number' || type === 'string') && (
          <Input
            value={cfg[nskey]}
            type={type === 'number' ? 'number' : 'text'}
            onChange={(ev, { value }) => {
              ev.preventDefault();

              const v =
                type === 'number'
                  ? float
                    ? parseFloat(value)
                    : parseInt(value, 10)
                  : value.toString();

              if (type === 'number' && isNaN(v as number)) return;

              optionChange(nskey, v as any);
            }}
            {...rest}
          />
        )}
        {help && <div className="muted">{help}</div>}
      </Form.Field>
      {children}
    </>
  ) : null;
}

function GeneralPane() {
  const [blur, setBlur] = useRecoilState(AppState.blur);

  const [cfg, setConfig] = useConfig({
    'gallery.auto_rate_on_favorite': undefined as boolean,
    'gallery.pages_to_read': undefined as number,
    'gallery.external_image_viewer': undefined as string,
    'gallery.external_image_viewer_args': undefined as string,
    'gallery.send_path_to_first_file': undefined as boolean,
    'gallery.send_extracted_archive': undefined as boolean,
    'this.language': undefined as number,
    'search.regex': undefined as boolean,
    'search.case_sensitive': undefined as boolean,
    'search.match_exact': undefined as boolean,
    'search.match_all_terms': undefined as boolean,
    'search.children': undefined as boolean,
  });

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  return (
    <Segment basic>
      <Form>
        <Header size="small" dividing>{t`View`}</Header>
        <Segment>
          <Form.Field>
            <Checkbox
              toggle
              label={t`Blur`}
              checked={blur}
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setBlur(checked);
              }, [])}
            />
            <div className="muted">{t`Blurs gallery and and collection covers across the application`}</div>
          </Form.Field>
          <OptionField
            isolation="client"
            label={t`Select language`}
            visible
            cfg={cfg}
            nskey="this.language"
            options={[
              { key: 'en', value: 'en', text: 'English' },
              { key: 'zh', value: 'zh', text: '中文' },
            ]}
            placeholder={t`Select language`}
            type="select"
            optionChange={optionChange}>
            <a
              href="https://happypandax.github.io/translation.html"
              target="_blank"
              rel="noopener noreferrer">
              {t`Not satisfied with the translation? Consider helping out! Click here for more information.`}
            </a>
          </OptionField>
        </Segment>
        {namespaceExists(cfg, 'gallery') && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="user" />
              {t`Gallery`}
            </Header>
            <Segment>
              <OptionField
                label={t`Automatically set unrated gallery to max rating on favorite`}
                cfg={cfg}
                nskey="gallery.auto_rate_on_favorite"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`How many pages in percent has to be read before the gallery is considered read`}
                cfg={cfg}
                nskey="gallery.pages_to_read"
                float
                type="number"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
        {namespaceExists(cfg, 'search') && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="user" />
              {t`Search`}
              <Header.Subheader>{t`Default search settings`}</Header.Subheader>
            </Header>
            <Segment>
              <OptionField
                label={t`Case sensitive`}
                cfg={cfg}
                nskey="search.case_sensitive"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Regex`}
                cfg={cfg}
                nskey="search.regex"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Match terms exactly`}
                cfg={cfg}
                nskey="search.match_exact"
                type="boolean"
                optionChange={optionChange}
              />

              <OptionField
                label={t`Match all terms`}
                cfg={cfg}
                nskey="search.match_all_terms"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Match on children`}
                cfg={cfg}
                nskey="search.children"
                type="boolean"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
        {namespaceExists(cfg, 'gallery', ['gallery.external_image_viewer']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="user" />
              {t`External Viewer`}
            </Header>
            <Segment>
              <Form.Group>
                <OptionField
                  label={t`External Image Viewer`}
                  cfg={cfg}
                  placeholder={t`path/to/viewer.exe`}
                  nskey="gallery.external_image_viewer"
                  type="string"
                  optionChange={optionChange}
                  width={10}
                />
                <OptionField
                  label={t`External Image Viewer Arguments`}
                  cfg={cfg}
                  placeholder={t`Example: -a -X --force`}
                  nskey="gallery.external_image_viewer_args"
                  type="string"
                  width={6}
                  optionChange={optionChange}
                />
              </Form.Group>
              <OptionField
                label={t`Send path to first file in gallery folder`}
                cfg={cfg}
                nskey="gallery.send_path_to_first_file"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Extract gallery archive before sending path to external viewer`}
                cfg={cfg}
                nskey="gallery.send_extracted_archive"
                type="boolean"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
      </Form>
    </Segment>
  );
}

function NetworkPane() {
  return <Segment basic></Segment>;
}

function ServerPane() {
  const [cfg, setConfig] = useConfig({
    'core.trash_item_duration': undefined as number,
    'core.trash_send_to_systemtrash': undefined as boolean,
    'core.trash_item_delete_files': undefined as boolean,
  });

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  return (
    <Segment basic>
      <Form>
        {namespaceExists(cfg, 'core', ['core.trash_send_to_systemtrash']) && (
          <>
            <Header size="small" dividing>
              {t`Trash`}
            </Header>
            <Segment>
              <OptionField
                label={t`Delete associated files on-disk when an item is pruned from trash`}
                cfg={cfg}
                nskey="core.trash_item_delete_files"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Send deleted files to the OS recycle bin when pruned from trash`}
                cfg={cfg}
                nskey="core.trash_send_to_systemtrash"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`How many hours an item should stay in the trash (per item) before it is deleted and removed PERMANENTLY`}
                cfg={cfg}
                nskey="core.trash_item_duration"
                type="number"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
      </Form>
    </Segment>
  );
}

function ImportPane() {
  const [cfg, setConfig] = useConfig({
    'import.add_to_inbox': undefined as boolean,
    'import.fail_on_move_error': undefined as boolean,
    'import.move_gallery': undefined as boolean,
    'import.move_copy': undefined as boolean,
    'import.move_dir': undefined as string,
    'import.skip_existing_galleries': undefined as boolean,
    'import.send_to_metadata_queue': undefined as boolean,
    'watch.enable': undefined as boolean,
    'watch.scan_on_startup': undefined as boolean,
    'watch.auto_add': undefined as boolean,
    'watch.network': undefined as string[],
    'watch.dirs': undefined as string[],
    'watch.ignore': undefined as string[],
  });

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  return (
    <Segment basic>
      <Form>
        {namespaceExists(cfg, 'watch') && (
          <>
            <Header dividing>
              <IsolationLabel isolation="user" />
              {t`Import & scan`}
              <Header.Subheader>{t`Default import settings`}</Header.Subheader>
            </Header>
            <Segment>
              <OptionField
                label={t`Add to Inbox after import`}
                cfg={cfg}
                nskey="import.add_to_inbox"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Skip existing galleries during scan`}
                cfg={cfg}
                nskey="import.skip_existing_galleries"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Add gallery to metadata queue after import`}
                cfg={cfg}
                nskey="import.send_to_metadata_queue"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Move gallery source`}
                help={t`Move the gallery files to a new location`}
                cfg={cfg}
                nskey="import.move_gallery"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Don't add gallery if the move or copy failed`}
                cfg={cfg}
                nskey="import.fail_on_move_error"
                disabled={!cfg['import.move_gallery']}
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Copy gallery source instead of move`}
                help={t`Copy the gallery files without moving the original files`}
                cfg={cfg}
                disabled={!cfg['import.move_gallery']}
                nskey="import.move_copy"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Folder to move gallery files to`}
                cfg={cfg}
                disabled={!cfg['import.move_gallery']}
                nskey="import.move_dir"
                type="string"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}

        {namespaceExists(cfg, 'watch') && (
          <>
            <Header size="small" dividing>
              {t`Watch`}
            </Header>
            <Segment>
              <OptionField
                label={t`Watch for new galleries`}
                cfg={cfg}
                nskey="watch.enable"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Scan for new galleries on startup`}
                cfg={cfg}
                nskey="watch.scan_on_startup"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Automatically import found galleries`}
                cfg={cfg}
                nskey="watch.auto_add"
                type="boolean"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
      </Form>
    </Segment>
  );
}

function AdvancedPane() {
  return <Segment basic></Segment>;
}

export function SettingsTab() {
  const [cfg] = useConfig();

  return (
    <Tab
      menu={useMemo(
        () => ({
          pointing: true,
          secondary: true,
          stackable: true,
        }),
        []
      )}
      panes={useMemo(
        () =>
          [
            {
              menuItem: {
                key: 'general',
                icon: 'cog',
                content: t`General`,
              },
              render: () => (
                <Tab.Pane
                  attached={undefined}
                  basic
                  className="no-padding-segment">
                  <GeneralPane />
                </Tab.Pane>
              ),
            },
            namespaceExists(cfg, 'import')
              ? {
                  menuItem: {
                    key: 'import',
                    icon: 'plus',
                    content: t`Import`,
                  },
                  render: () => (
                    <Tab.Pane
                      attached={undefined}
                      basic
                      className="no-padding-segment">
                      <ImportPane />
                    </Tab.Pane>
                  ),
                }
              : null,
            namespaceExists(cfg, 'plugin')
              ? {
                  menuItem: {
                    key: 'plugins',
                    icon: 'cubes',
                    content: t`Plugins`,
                  },
                  render: () => (
                    <Tab.Pane
                      attached={undefined}
                      basic
                      className="no-padding-segment">
                      <NetworkPane />
                    </Tab.Pane>
                  ),
                }
              : null,
            {
              menuItem: {
                key: 'network',
                icon: 'project diagram',
                content: t`Network`,
              },
              render: () => (
                <Tab.Pane
                  attached={undefined}
                  basic
                  className="no-padding-segment">
                  <NetworkPane />
                </Tab.Pane>
              ),
            },
            {
              menuItem: {
                key: 'server',
                icon: <Icon className="hpx-standard" />,
                content: t`Server`,
              },
              render: () => (
                <Tab.Pane
                  attached={undefined}
                  basic
                  className="no-padding-segment">
                  <ServerPane />
                </Tab.Pane>
              ),
            },
            {
              menuItem: {
                key: 'advanced',
                icon: 'exclamation triangle',
                content: t`Advanced`,
              },
              render: () => (
                <Tab.Pane
                  attached={undefined}
                  basic
                  className="no-padding-segment">
                  <AdvancedPane />
                </Tab.Pane>
              ),
            },
          ].filter(Boolean),
        []
      )}
    />
  );
}

export default function SettingsModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  return (
    <Modal
      dimmer="inverted"
      closeIcon
      {...props}
      className={classNames('min-400-h', className)}>
      <Modal.Header>
        <Icon name="settings" />
        {t`Preferences`}
      </Modal.Header>
      <Modal.Content as={Segment} className="no-margins" basic>
        <SettingsTab />
      </Modal.Content>
    </Modal>
  );
}
