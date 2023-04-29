import classNames from 'classnames';
import { useRouter } from 'next/router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import {
  Checkbox,
  Divider,
  Form,
  FormFieldProps,
  Header,
  Icon,
  Input,
  Label,
  Message,
  Modal,
  Segment,
  Select,
  Tab,
} from 'semantic-ui-react';

import { useConfig } from '../client/hooks/settings';
import t from '../client/lang';
import { defined } from '../shared/utility';
import { AppState, MiscState } from '../state';
import { JSONTextEditor } from './misc';
import { ModalWithBack } from './misc/BackSupport';

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

export function IsolationLabel({
  isolation,
  ...props
}: {
  isolation: 'user' | 'client' | 'server';
} & React.ComponentProps<typeof Label>) {
  return (
    <Label
      horizontal
      basic={isolation === 'server'}
      size="mini"
      title={
        isolation === 'user'
          ? t`This option is isolated to the user`
          : isolation === 'client'
          ? t`This option is isolated to the client`
          : t`This option is global`
      }
      color={
        isolation === 'user'
          ? 'purple'
          : isolation === 'client'
          ? 'teal'
          : 'black'
      }
      {...props}>
      {isolation === 'user'
        ? t`User`
        : isolation === 'client'
        ? t`Client`
        : t`Global`}
    </Label>
  );
}

export function OptionField<
  T extends Record<string, any>,
  K extends keyof T,
  I extends 'select' | 'number' | 'boolean' | 'string' | 'json'
>({
  nskey,
  label,
  inputLabel,
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
  inputLabel?: string;
  help?: string;
  float?: boolean;
  width?: FormFieldProps['width'];
  isolation?: 'user' | 'client' | 'server';
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
    : I extends 'json'
    ? React.ComponentProps<typeof JSONTextEditor>
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
              <label>
                {' '}
                {isolation && <IsolationLabel isolation={isolation} />} {label}
              </label>
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
            label={
              inputLabel ? { basic: true, content: inputLabel } : undefined
            }
            size="mini"
            labelPosition={inputLabel ? 'right' : undefined}
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
        {type === 'json' && (
          <JSONTextEditor
            tabIndex={
              rest.tabIndex ? parseInt(rest.tabIndex as string, 10) : undefined
            }
            value={cfg[nskey]}
            onChange={(v) => {
              optionChange(nskey, v as any);
            }}
            {...rest}
          />
        )}
        {help && <div className="sub-text">{help}</div>}
      </Form.Field>
      {children}
    </>
  ) : null;
}

function GeneralPane() {
  const [blur, setBlur] = useRecoilState(AppState.blur);
  const [theme, setTheme] = useRecoilState(AppState.theme);
  const [drawerButtonPosition, setDrawerButtonPosition] = useRecoilState(
    AppState.drawerButtonPosition
  );
  const [sidebarForcePosition, setSidebarForcePosition] = useRecoilState(
    AppState.sidebarForcePosition
  );

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
        <Header size="small" dividing>{t`Web Client`}</Header>
        <Segment>
          <Form.Field>
            <label>
              <IsolationLabel isolation="client" /> {t`Select theme`}
            </label>
            <Select
              options={[
                { key: 'momo-l', value: 'momo-l', text: 'Momo (Light)' },
                {
                  key: 'momo-d',
                  value: 'momo-d',
                  text: 'Momo (Dark)',
                },
              ]}
              value={theme}
              placeholder={t`Select theme`}
              onChange={useCallback((ev, { value }) => {
                ev.preventDefault();
                if (value) setTheme(value as any);
              }, [])}
            />
          </Form.Field>
          <Form.Field>
            <Checkbox
              toggle
              label={
                <label>
                  <IsolationLabel isolation="client" /> {t`Blur`}
                </label>
              }
              checked={blur}
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setBlur(checked);
              }, [])}
            />
            <div className="muted">{t`Blurs gallery and and collection covers across the application`}</div>
          </Form.Field>
          <Form.Field>
            <label>
              <IsolationLabel isolation="client" /> {t`Drawer button position`}
            </label>
            <Select
              options={[
                { key: 'left', value: 'left', text: t`Left` },
                { key: 'right', value: 'right', text: t`Right` },
              ]}
              value={drawerButtonPosition}
              placeholder={t`Select position`}
              onChange={useCallback((ev, { value }) => {
                ev.preventDefault();
                if (value) setDrawerButtonPosition(value as any);
              }, [])}
            />
          </Form.Field>
          <Form.Field>
            <label>
              <IsolationLabel isolation="client" /> {t`Sidebar position`}
            </label>
            <Select
              options={[
                { key: 'auto', value: 'auto', text: t`Auto` },
                { key: 'left', value: 'left', text: t`Left` },
                { key: 'right', value: 'right', text: t`Right` },
              ]}
              value={sidebarForcePosition ?? 'auto'}
              placeholder={t`Select position`}
              onChange={useCallback((ev, { value }) => {
                ev.preventDefault();
                setSidebarForcePosition(
                  value === 'auto' ? undefined : (value as any)
                );
              }, [])}
            />
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
            <Segment clearing>
              <OptionField
                label={t`Set unrated gallery to maximum rating when favorited`}
                cfg={cfg}
                nskey="gallery.auto_rate_on_favorite"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`What percentage of pages must be read to consider the gallery as read?`}
                cfg={cfg}
                nskey="gallery.pages_to_read"
                float
                type="number"
                inputLabel="%"
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
            <Segment clearing>
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
    'core.backup_dir': undefined as string,
    'core.backup_on_update': undefined as boolean,
    'core.auto_backup_interval': undefined as number,
    'core.check_new_releases': undefined as boolean,
    'core.auto_install_release': undefined as boolean,
    'core.check_release_interval': undefined as number,
    'core.allow_alpha_releases': undefined as boolean,
    'core.allow_beta_releases': undefined as boolean,
    'server.name': undefined as string,
    'server.session_span': undefined as number,
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
        <Segment clearing>
          <IsolationLabel attached="top left" isolation="server" />
          <OptionField
            label={t`Server name`}
            cfg={cfg}
            nskey="server.name"
            type="string"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Amount of time a session is valid for`}
            cfg={cfg}
            nskey="server.session_span"
            type="number"
            help={`Set to 0 for always valid`}
            inputLabel={t`minutes`}
            optionChange={optionChange}
          />
        </Segment>
        {namespaceExists(cfg, 'core', ['core.check_new_releases']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="server" />
              {t`Updates`}
            </Header>
            <Segment clearing>
              <OptionField
                label={t`Regularly check for updates`}
                cfg={cfg}
                nskey="core.check_new_releases"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Automatically download, install and restart when a new update is available`}
                cfg={cfg}
                nskey="core.auto_install_release"
                disabled={!cfg?.['core.check_new_releases']}
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Interval in minutes between checking for a new update`}
                cfg={cfg}
                nskey="core.check_release_interval"
                type="number"
                disabled={!cfg?.['core.check_new_releases']}
                help={`Set to 0 to only check once every startup`}
                inputLabel={t`minutes`}
                optionChange={optionChange}
              />
              <OptionField
                label={t`Allow downloading beta releases`}
                cfg={cfg}
                disabled={!cfg?.['core.check_new_releases']}
                nskey="core.allow_beta_releases"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Allow downloading alpha releases`}
                cfg={cfg}
                disabled={!cfg?.['core.check_new_releases']}
                nskey="core.allow_alpha_releases"
                type="boolean"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
        {namespaceExists(cfg, 'core', ['core.backup_dir']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="server" />
              {t`Backup`}
            </Header>
            <Segment clearing>
              <OptionField
                label={t`Interval in hours between automatically creating a backup`}
                cfg={cfg}
                nskey="core.auto_backup_interval"
                type="number"
                help={`Set to 0 to disable auto backup`}
                inputLabel={t`hours`}
                optionChange={optionChange}
              />
              <OptionField
                label={t`Backup directory`}
                cfg={cfg}
                nskey="core.backup_dir"
                type="string"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Create a backup before applying a new update`}
                cfg={cfg}
                nskey="core.backup_on_update"
                type="boolean"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
        {namespaceExists(cfg, 'core', ['core.trash_send_to_systemtrash']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="server" />
              {t`Trash`}
            </Header>
            <Segment clearing>
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
                disabled={!cfg?.['core.trash_item_delete_files']}
                nskey="core.trash_send_to_systemtrash"
                type="boolean"
                optionChange={optionChange}
              />
              <OptionField
                label={t`How many hours an item should stay in the trash before it is deleted and removed PERMANENTLY`}
                cfg={cfg}
                disabled={!cfg?.['core.trash_item_delete_files']}
                help={`This is applied on a per-item basis`}
                nskey="core.trash_item_duration"
                type="number"
                inputLabel={t`hours`}
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
                help={t`Move the gallery files to a specified location`}
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
              <IsolationLabel isolation="server" />
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
  const [cfg, setConfig] = useConfig({
    'core.debug': undefined as boolean,
    'core.report_critical_errors': undefined as boolean,
    'core.concurrent_image_tasks': undefined as number,
    'core.concurrent_network_tasks': undefined as number,
    'core.auto_thumb_clean_size': undefined as number,
    'core.auto_pages_clean_size': undefined as number,
    'core.auto_temp_clean_size': undefined as number,
    'core.cache_expiration_time': undefined as number,
    'core.interface_cache_time': undefined as number,
    'core.message_cache_time': undefined as number,
    'download.size': undefined as number,
    'advanced.enable_auto_indexing': undefined as boolean,
    'advanced.enable_cache': undefined as boolean,
    'advanced.crop_wide_thumbnails': undefined as boolean,
    'advanced.crop_thumbnail_alignment': undefined as number,
    'core.auto_cache_clean_size': undefined as number,
  });

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  return (
    <Segment basic>
      <Message warning>
        <Icon name="warning sign" />
        Momo: {t`Please be careful with these settings!`}
      </Message>
      <Form>
        <Segment>
          <IsolationLabel attached="top left" isolation="server" />
          <OptionField
            label={t`Enable debug mode`}
            cfg={cfg}
            nskey="core.debug"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Report critical errors so they can be fixed`}
            cfg={cfg}
            help={t`Momo: Don't complain about errors if you turn this off! ٩(๑ \`н´๑)۶`}
            nskey="core.report_critical_errors"
            type="boolean"
            optionChange={optionChange}
          />
          <Divider />
          <OptionField
            label={t`Automatically index new or updated items`}
            cfg={cfg}
            nskey="advanced.enable_auto_indexing"
            type="boolean"
            optionChange={optionChange}
          />
          <Divider />
          <OptionField
            label={t`Crop wide thumbnails`}
            cfg={cfg}
            nskey="advanced.crop_wide_thumbnails"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Wide thumbnails crop alignment`}
            cfg={cfg}
            nskey="advanced.crop_thumbnail_alignment"
            type="number"
            help={t`A number between 0 (left) to 1 (right)`}
            optionChange={optionChange}
          />
        </Segment>

        {namespaceExists(cfg, 'core', ['core.concurrent_image_tasks']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="server" />
              {t`Tasks`}
              <Header.Subheader>{t`Note that changing these does not necessarily increase perfomance`}</Header.Subheader>
            </Header>
            <Segment clearing>
              <OptionField
                label={t`Amount of download tasks allowed to run concurrently`}
                cfg={cfg}
                nskey="download.size"
                type="number"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Amount of image generation tasks allowed to run concurrently`}
                cfg={cfg}
                nskey="core.concurrent_image_tasks"
                type="number"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Amount of network requests allowed to run concurrently`}
                cfg={cfg}
                nskey="core.concurrent_network_tasks"
                type="number"
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}

        {namespaceExists(cfg, 'core', ['core.auto_thumb_clean_size']) && (
          <>
            <Header size="small" dividing>
              <IsolationLabel isolation="server" />
              {t`Cache`}
            </Header>
            <Segment clearing>
              <OptionField
                label={t`Auto-clean thumbnail cache when it exceeds this size`}
                cfg={cfg}
                nskey="core.auto_thumb_clean_size"
                type="number"
                help={t`For small image thumbnails, like gallery covers`}
                inputLabel="MB"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Auto-clean pages cache when it exceeds this size`}
                cfg={cfg}
                nskey="core.auto_pages_clean_size"
                type="number"
                inputLabel="MB"
                help={t`For downsized versions of the original page images`}
                optionChange={optionChange}
              />
              <OptionField
                label={t`Auto-clean temporary cache when it exceeds this size`}
                cfg={cfg}
                nskey="core.auto_temp_clean_size"
                type="number"
                help={t`For temporary files, these are usually deleted after a short time`}
                inputLabel="MB"
                optionChange={optionChange}
              />
              <OptionField
                label={t`Auto-clean cache when it exceeds this size`}
                cfg={cfg}
                nskey="core.auto_cache_clean_size"
                type="number"
                help={t`For long-term cached files or other files that don't fit in the other categories`}
                inputLabel="MB"
                optionChange={optionChange}
              />

              <Form.Field>
                <Divider section />
              </Form.Field>

              <OptionField
                label={t`Enable data cache`}
                cfg={cfg}
                nskey="advanced.enable_cache"
                type="boolean"
                help={t`This will cache requested data, sometimes reducing the amount of processing done on the server`}
                optionChange={optionChange}
              />

              <OptionField
                label={t`Cache TTL in seconds`}
                cfg={cfg}
                nskey="core.cache_expiration_time"
                type="number"
                disabled={!cfg?.['advanced.enable_cache']}
                inputLabel={t`seconds`}
                optionChange={optionChange}
              />
              <OptionField
                label={t`Client interface Cache TTL in seconds`}
                cfg={cfg}
                nskey="core.interface_cache_time"
                type="number"
                disabled={!cfg?.['advanced.enable_cache']}
                inputLabel={t`seconds`}
                optionChange={optionChange}
              />
              <OptionField
                label={t`Client API Cache TTL in seconds`}
                cfg={cfg}
                nskey="core.message_cache_time"
                type="number"
                disabled={!cfg?.['advanced.enable_cache']}
                inputLabel={t`seconds`}
                optionChange={optionChange}
              />
            </Segment>
          </>
        )}
      </Form>
    </Segment>
  );
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
            {
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
            },
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

function RestartNeededSegment({ settings = [] }: { settings: string[] }) {
  const touched = useRecoilValue(MiscState.touchedConfig);

  return settings.map((s) => touched.includes(s)).some(Boolean) ? (
    <Message
      as={Segment}
      attached="top"
      tertiary
      className="no-margins"
      warning>
      <Icon name="warning circle" />
      {t`Some settings require a server restart to take effect.`}
    </Message>
  ) : null;
}

export default function SettingsModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  const [open, setOpen] = useState(false);

  const touched = useRecoilValue(MiscState.touchedConfig);
  const touchedRef = useRef(touched);

  const router = useRouter();
  useEffect(() => {
    touchedRef.current = touched;
  }, [touched]);

  useEffect(() => {
    if (open) {
      return () => {
        if (
          ['this.language']
            .map((s) => touchedRef.current.includes(s))
            .some(Boolean)
        ) {
          router.reload();
        }
      };
    }
    return () => {};
  }, [open]);

  return (
    <ModalWithBack
      dimmer="inverted"
      closeIcon
      centered={false}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      {...props}
      className={classNames('min-400-h', className)}>
      <Modal.Header>
        <Icon name="settings" />
        {t`Preferences`}
      </Modal.Header>
      <RestartNeededSegment
        settings={[
          'core.concurrent_image_tasks',
          'core.debug',
          'core.concurrent_network_tasks',
          'server.name',
          'plugin.dev',
          'plugin.plugin_dir',
        ]}
      />
      <Modal.Content as={Segment} className="no-margins" basic>
        <SettingsTab />
      </Modal.Content>
    </ModalWithBack>
  );
}
