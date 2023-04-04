import { GetServerSidePropsResult, NextPageContext } from 'next';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useDebounce, useList, useMap } from 'react-use';
import { useRecoilValue } from 'recoil';
import {
  Button,
  Container,
  Divider,
  Form,
  Icon,
  Input,
  Label,
  List,
  Message,
  Popup,
  Segment,
  Select,
} from 'semantic-ui-react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import {
  EmptySegment,
  JSONTextEditor,
  Markdown,
  PageTitle,
} from '../../components/misc';
import { TransientFileView } from '../../components/transient/FileView';
import { ImportViews } from '../../components/transient/ImportView';
import { TransientView } from '../../components/transient/index';
import { ServiceType } from '../../server/constants';
import {
  CommandState,
  TransientViewSubmitAction,
  TransientViewType,
} from '../../shared/enums';
import {
  CommandID,
  TransientView as TransientViewT,
  ViewID,
} from '../../shared/types';
import { ImportState } from '../../state';
import AddPage from './index';

function PathPattern({ onChange }: { onChange?: (value: string) => void }) {
  const { mutate, error, data } = useMutationType(
    MutatationType.RESOLVE_PATH_PATTERN,
    { retry: false }
  );

  const [pattern, setPattern] = useState('');
  const [showPattern, setShowPattern] = useState(false);

  useDebounce(
    () => {
      if (pattern) {
        mutate({
          pattern,
          __options: {
            notifyError: false,
          },
        });
      }
    },
    2000,
    [pattern]
  );

  return (
    <Segment basic className="no-padding-segment no-margins">
      <Input
        fluid
        error={!!error}
        size="mini"
        placeholder="{**}/{gallery}"
        value={pattern}
        onChange={useCallback(
          (e, v) => {
            e.preventDefault();
            setPattern(v.value);
            onChange?.(v.value);
          },
          [onChange]
        )}
      />

      <Divider horizontal>
        {!!error && (
          <Label basic color="red">
            {error?.response?.data?.error}
          </Label>
        )}
        {!error && !!data && (
          <Label
            as="a"
            size="tiny"
            onClick={() => setShowPattern(!showPattern)}
          >
            <Icon name={showPattern ? 'eye slash' : 'eye'} />
            {t`Compiled`}
          </Label>
        )}
      </Divider>
      {showPattern && (
        <Segment>
          <JSONTextEditor
            pretty
            readOnly
            value={data?.data}
            className="max-400-h overflow-auto"
          />
        </Segment>
      )}
    </Segment>
  );
}

interface PageProps {
  views: TransientViewT<any>[];
}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<{}>> {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  const views = await server.transient_views({});

  return {
    props: { views },
  };
}

export default function Page({ views }: PageProps) {
  const stateKey = 'import';

  const [error, setError] = useState('');
  const [path, setPath] = useState('');
  const [scanViewId, setScanViewId] = useState<ViewID>();
  const [scanCmdId, setScanCmdId] = useState<CommandID<any>>();
  const [submitting, setSubmitting] = useState(false);

  const activeImportView = useRecoilValue(
    ImportState.activeImportView(stateKey)
  );

  const [reScanLoading, { set: setRescanLoading }] = useMap<
    Record<ViewID, boolean>
  >({});
  const [patterns, { removeAt, updateAt, push }] = useList([] as string[]);

  const actions =
    useRef<Unwrap<React.ComponentProps<typeof TransientView>['actions']>>();

  // have to use useRef and NOT useMap or we risk causing a state change update loop
  const viewsMap = useRef(
    views.reduce((acc, v) => {
      acc[v.id] = v;
      return acc;
    }, {} as Record<ViewID, Unwrap<typeof views>>)
  );

  const { data, refetch } = useQueryType(
    QueryType.TRANSIENT_VIEWS,
    {},
    { initialData: views }
  );

  const {
    mutateAsync: scanGalleriesAsync,
    mutate: scanGalleries,
    data: scanData,
  } = useMutationType(MutatationType.SCAN_GALLERIES, {
    onMutate: () => {
      setError('');
    },
    onError: (e) => {
      setError(e?.response?.data?.error);
    },
  });

  const checkRescanLoading = useCallback(
    (d: typeof views) => {
      d.forEach?.((v) => {
        const loading = v.state === CommandState.Started;
        if (reScanLoading[v.id] !== loading) {
          setRescanLoading(v.id, loading);
        }
      });
    },
    [reScanLoading]
  );

  useCommand(
    scanData?.data,
    {
      onError: (e) => {
        setError(e.error);
        setSubmitting(false);
      },
      requestOptions: { notifyError: false },
    },
    (r) => {
      setScanCmdId(r.command_id);
      setSubmitting(false);
      refetch().then(() => {
        // try again for good measure
        setTimeout(() => {
          refetch();
        }, 1500);
      });
      setPath('');
    },
    []
  );

  useCommand(
    scanCmdId,
    {
      onError: (e) => {
        setError(e.error);
      },
      requestOptions: { notifyError: false },
    },
    (r) => {
      refetch();
    },
    []
  );

  useEffect(() => {
    checkRescanLoading(data?.data);
  }, [data]);

  useEffect(() => {
    if (scanViewId) {
      if (!data?.data?.find?.((v) => v.id === scanViewId)) {
        setScanViewId(undefined);
      }
    }
  }, [data, scanViewId]);

  let root = path;
  if (root.length > 100) {
    root = '...' + path.slice(path.length - 100);
  }
  if (!root.endsWith('/') && !root.endsWith('\\')) {
    root += root.includes('/') ? '/' : '\\';
  }

  const fileViewsOptions = data?.data
    ?.filter?.((v) => v.type === TransientViewType.File)
    ?.map?.((v) => {
      return { key: v.id, value: v.id, text: v.id };
    });

  return (
    <AddPage>
      <PageTitle title={t`Scan directories`} />
      <Container as={Segment}>
        <Form
          error={!!error}
          onSubmit={useCallback(
            (e) => {
              e.preventDefault();
              setSubmitting(true);
              scanGalleries({
                path,
                patterns,
                view_id: scanViewId,
                __options: { notifyError: false },
              });
            },
            [path, patterns, scanViewId]
          )}
        >
          <Form.Input
            //   type="text"
            action
            value={path}
            onChange={(e, { value }) => setPath(value)}
            placeholder={t`Directory`}
          >
            <input />
            <Select
              options={[
                { text: t`Create new view`, value: 0 },
                ...fileViewsOptions,
              ]}
              onChange={useCallback((e, { value }) => {
                e.preventDefault();
                if (value === 0) {
                  setScanViewId(undefined);
                } else {
                  setScanViewId(value as ViewID);
                }
              }, [])}
              compact
              value={scanViewId === undefined ? 0 : scanViewId}
            />
            <Button
              loading={submitting}
              disabled={!path}
              primary
              type="submit"
              title={t`Submit`}
            >
              <Icon name="search" />
              {t`Scan`}
            </Button>
          </Form.Input>
          <Message error>{error}</Message>
        </Form>
        <Divider />
        <List size="tiny" relaxed>
          <List.Item>
            <Button
              size="mini"
              onClick={useCallback((e, v) => {
                e.preventDefault();
                push('');
              }, [])}
            >
              <Icon name="plus" /> {t`Add pattern`}
            </Button>
            ⸻{root}
            <Label basic color="black">
              {t`<pattern>`}
            </Label>
            <Popup
              on="click"
              wide="very"
              position="bottom right"
              trigger={<Button circular basic size="mini" icon="help" />}
            >
              <Markdown>
                {t`#### Path patterns
                    Path patterns are rules used to match directories and files in the scanning process. See [the documentation](https://happypandax.github.io/faq.html#scanning-for-galleries) for details.
                    
                    A pattern must be enclosed in curly braces to be recognized. 

                    Several **item** tokens exist to specify what item to extract from a path tree. No duplicate **item** tokens are allowed:
                    - \`{collection}\`: The collection
                    - \`{series}\` or \`{grouping}\`: The series
                    - \`{circle}\`: The circle
                    - \`{category}\`: The category
                    - \`{language}\`: The language
                    - \`{parody}\`: The parody
                    - \`{artist}\`: The artist
                    - \`{gallery}\`: The gallery. Note that the last component in the path must be the gallery item token.

                    **Glob** patterns are used to match file or directory names (see [wikipedia](https://en.wikipedia.org/wiki/Glob_%28programming%29) for details):

                    | Pattern | Matches |
                    | --- | --- |
                    | \`{Law*}\` | Law, Laws, or Lawyer |
                    | \`{*Law*}\` | Law, GrokLaw, or Lawyer |
                    | \`{?at}\` |  	Cat, cat, Bat or bat |
                    | \`{[CB]at}\` | Cat or Bat |
                    | \`{*}\` | Match any text |
                    | \`{**}\` |  Recursively match any number of layers of non-hidden directories (Can only be used once) |

                    
                    **Regex** patterns can be used instead of globbing to match file or directory names. To use a regex pattern, enclose it inside two \`%\`
                    for example: \`{%Comiket \\d+%}\`

                    To combine a glob pattern or regex pattern with an item token, use \`:\` to separate the two. For example: \`{collection: %Comiket \\d+%}\`

                    Some **examples**:
                    - \`root/{collection: %Comiket \\d+%}/{series}/{gallery}\`: Match all directories with names matching \`Comiket \\d+\` as collections, then match all directions as series, then match all directories or files as galleries.
                    - \`root/{artist}/{series}/\`: Inside root/ match all directories as artists, then match all directions as series. \`{gallery}\` as the last component is implicitly added here.
                    - \`root/{gallery}/momo/\`: **ERROR** - The last component must be the gallery item token.
                    - \`root/{artist}/momo/{gallery}\`: **OK** - The last component is the gallery item token.
                    - \`*/{gallery}\`: **WARNING** - \`*\` will not be treated as a wildcard character because it is not enclosed in curly braces.
                    - \`{**}/{gallery}\`: This is the default pattern. It traverses all directories recursively to the last component that could pass off as gallery.
                    `}
              </Markdown>
            </Popup>
          </List.Item>
          {patterns.map((p, idx) => (
            <List.Item key={`${idx}`}>
              <List.Icon
                link
                name="close"
                color="red"
                className="centered-container"
                onClick={() => removeAt(idx)}
              />
              <List.Content>
                <PathPattern onChange={(v) => updateAt(idx, v)} />
              </List.Content>
            </List.Item>
          ))}
        </List>
        <Segment>
          <Label basic attached="top">{t`Scan views`}</Label>
          <List divided relaxed>
            {!data?.data?.length && <EmptySegment />}
            {!!data &&
              data.data
                .filter((d) => d.type === TransientViewType.File)
                .map((view) => (
                  <TransientFileView
                    defaultOpen={data.data.length === 1}
                    submitAction={TransientViewSubmitAction.SendToView}
                    submitValue={activeImportView}
                    key={view.id}
                    actions={actions}
                    data={view}
                    onDeleteItem={() => {
                      refetch();
                      actions.current?.refetch?.();
                    }}
                    onRemove={() =>
                      refetch().then(() =>
                        // try again for good measure
                        setTimeout(() => {
                          refetch();
                        }, 1500)
                      )
                    }
                    onSubmit={() =>
                      refetch().then(() =>
                        // try again for good measure
                        setTimeout(() => {
                          refetch();
                        }, 1500)
                      )
                    }
                    onData={(v) => {
                      viewsMap[view.id] = v;
                      checkRescanLoading(Object.values(viewsMap));
                    }}
                    label={t`Scanned items`}
                    labelButtons={
                      <Button
                        secondary
                        floated="right"
                        size="mini"
                        loading={reScanLoading?.[view.id]}
                        disabled={reScanLoading?.[view.id]}
                        compact
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          const v = viewsMap.current?.[view.id];
                          if (v) {
                            const patterns =
                              (v.properties?.patterns as string[]) ?? [];

                            v.roots.forEach((path) => {
                              scanGalleriesAsync({
                                path,
                                patterns,
                                options: v.options,
                                view_id: v.id,
                              }).finally(() => refetch());
                            });

                            setRescanLoading(v.id, true);
                          }
                        }}
                      >
                        <Icon name="refresh" />
                        {t`Rescan`}
                      </Button>
                    }
                  />
                ))}
          </List>
        </Segment>
        <ImportViews
          onRemove={() => refetch()}
          onSubmit={() => refetch()}
          submitAction={TransientViewSubmitAction.SendToDatabase}
          submitValue={activeImportView}
          data={data?.data?.filter?.(
            (d) => d.type === TransientViewType.Import
          )}
          stateKey={stateKey}
          onCreate={() => refetch()}
        />
      </Container>
    </AddPage>
  );
}
