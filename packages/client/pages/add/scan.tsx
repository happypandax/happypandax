import { useCallback, useState } from 'react';
import { useDebounce, useList } from 'react-use';
import {
  Button,
  Container,
  Divider,
  Form,
  Icon,
  Input,
  Label,
  List,
  Popup,
  Segment,
} from 'semantic-ui-react';

import { MutatationType, useMutationType } from '../../client/queries';
import { JSONTextEditor, Markdown, PageTitle } from '../../components/misc';
import t from '../../misc/lang';
import { ItemBasePage } from './item';

function PathPattern({ onChange }: { onChange?: (value: string) => void }) {
  const {
    mutate,
    error,
    data,
  } = useMutationType(MutatationType.RESOLVE_PATH_PATTERN, { retry: false });

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
            onClick={() => setShowPattern(!showPattern)}>
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

export default function Page() {
  const [path, setPath] = useState('');
  const [patterns, { removeAt, updateAt, push }] = useList([] as string[]);

  let root = path;
  if (root.length > 100) {
    root = '...' + path.slice(path.length - 100);
  }
  if (!root.endsWith('/') && !root.endsWith('\\')) {
    root += '/';
  }

  return (
    <ItemBasePage>
      <PageTitle title={t`Scan directories`} />
      <Container as={Segment}>
        <Form
          onSubmit={useCallback((e) => {
            e.preventDefault();
            setPath('');
          }, [])}>
          <Form.Input
            //   type="text"
            action
            value={path}
            onChange={(e, { value }) => setPath(value)}
            placeholder={t`Directory`}>
            <input />
            <Button disabled={!path} primary type="submit" title={t`Submit`}>
              <Icon name="upload" />
              {t`Submit`}
            </Button>
          </Form.Input>
        </Form>
        <Divider />
        <List size="tiny" relaxed>
          <List.Item>
            <Button
              size="mini"
              onClick={useCallback((e, v) => {
                e.preventDefault();
                push('');
              }, [])}>
              <Icon name="plus" /> {t`Add pattern`}
            </Button>
            <Label basic color="black">
              {root}
              {t`<pattern>`}
            </Label>
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
          <List.Item>
            <Popup
              on="click"
              wide="very"
              position="bottom right"
              trigger={<Button circular size="mini" icon="help" />}>
              <Markdown>
                {t`#### Path patterns
                    Path patterns are used as rules to match directories to be scanned. See [the documentation](https://happypandax.github.io/faq.html#scanning-for-galleries) for details.
                    
                    A pattern must be enclosed in curly braces to be recognized. 

                    Several **item** tokens exist to specify what item to extract from a directory tree. No duplicate **item** tokens are allowed:
                    - \`{collection}\`: The collection
                    - \`{series}\` or \`{grouping}\`: The series
                    - \`{artist}\`: The artist
                    - \`{gallery}\`: The gallery. Note that the last component in the path must be the gallery item token.

                    **Glob** patterns are be used to match file or directory names (see [wiki](https://en.wikipedia.org/wiki/Glob_%28programming%29) for details):

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
                    - \`root/{collection: %Comiket \\d+%}/{series}/{gallery}\`: Match all directories with names matching \`Comiket \\d+\` as collections, then match all directions as series, then match all directories as galleries.
                    - \`root/{artist}/{series}/\`: Match all directories as artists, then match all directions as series. \`{gallery}\` as the last component is implied here.
                    - \`root/{gallery}/momo/\`: **ERROR** - The last component must be the gallery item token.
                    - \`root/{artist}/momo/{gallery}\`: **OK** - The last component is the gallery item token.
                    - \`*/{gallery}\`: **WARNING** - \`*\` will not be treated as a wildcard character because it is not enclosed in curly braces.
                    - \`{**}/{gallery}\`: This is the default pattern.
                    `}
              </Markdown>
            </Popup>
          </List.Item>
        </List>
      </Container>
    </ItemBasePage>
  );
}
