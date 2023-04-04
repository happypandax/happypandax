import classNames from 'classnames';
import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useHoverDirty } from 'react-use';
import {
  Button,
  Container,
  Divider,
  Form,
  Grid,
  Icon,
  Label,
  Portal,
  Segment,
  Select,
} from 'semantic-ui-react';

import AddPage from '../';
import t from '../../../client/lang';
import { FileDropZone } from '../../../components/misc';
import { StickySidebar } from '../../../components/Sidebar';
import { TransientImportView } from '../../../components/transient/ImportView';
import { FileT, SourceItem } from '../../../shared/types';

export async function getServerSideProps(context) {
  return {
    redirect: {
      destination: '/add/item/gallery',
      permanent: false,
    },
    props: {},
  };
}

export function FileSegment({
  onCreate,
}: {
  onCreate: (items: SourceItem[]) => boolean;
}) {
  const [files, setFiles] = useState<FileT[]>([]);
  const [path, setPath] = useState('');

  return (
    <Segment>
      <Form
        onSubmit={useCallback(
          (e) => {
            e.preventDefault();
            if (onCreate && onCreate([{ source: 'host', path }])) {
              setPath('');
            }
          },
          [onCreate, path]
        )}
      >
        <Form.Input
          type="text"
          action
          value={path}
          onChange={(e, { value }) => setPath(value)}
          placeholder={t`Load from path (path must exist on the host)`}
        >
          <input />
          <Button disabled={!path} primary type="submit" title={t`Create`}>
            <Icon name="plus" />
            {t`Create`}
          </Button>
        </Form.Input>
      </Form>
      <Divider horizontal>{t`Upload files/folders`}</Divider>
      <FileDropZone files={files} onFiles={setFiles} />
      {!!files.length && (
        <Divider horizontal>
          <Button
            primary
            onClick={(e) => {
              e.preventDefault();
              if (
                onCreate &&
                onCreate(files.map((f) => ({ source: 'file', file: f })))
              ) {
                setFiles([]);
              }
            }}
          >{t`Create`}</Button>
        </Divider>
      )}
    </Segment>
  );
}

export function Header({
  active,
}: {
  active: 'gallery' | 'collection' | 'series';
}) {
  return (
    <Segment basic textAlign="center">
      <Button.Group>
        <Link href="/add/item/gallery" passHref>
          <Button
            as="a"
            primary={active === 'gallery'}
            active={active === 'gallery'}
          >{t`Gallery`}</Button>
        </Link>
        <Button.Or />
        <Link href="/add/item/series" passHref>
          <Button
            as="a"
            primary={active === 'series'}
            active={active === 'series'}
          >{t`Series`}</Button>
        </Link>
        <Button.Or />
        <Link href="/add/item/collection" passHref>
          <Button
            as="a"
            primary={active === 'collection'}
            active={active === 'collection'}
          >{t`Collection`}</Button>
        </Link>
      </Button.Group>
    </Segment>
  );
}

function ViewSidebar() {
  const [expanded, setExpanded] = useState(false);
  const ref = useRef(null);

  const hovered = useHoverDirty(ref);

  useEffect(() => {
    if (hovered) {
      setExpanded(true);
    } else {
      setExpanded(false);
    }
  }, [hovered]);

  return (
    <Portal open>
      <StickySidebar
        ref={ref}
        className={classNames({ 'sticky-page-sidebar': expanded })}
        size={expanded ? 'very wide' : 'very thin'}
        visible={true}
        onHide={useCallback(() => {}, [])}
      >
        <Label attached="top">View</Label>
      </StickySidebar>
    </Portal>
  );
}

export function ItemBasePage({ children }: { children: React.ReactNode }) {
  return (
    <AddPage>
      <Container>
        {children}

        <TransientImportView defaultOpen />

        <Grid centered>
          <Grid.Row>
            <Select placeholder={t`Select import view`} />
          </Grid.Row>
        </Grid>
      </Container>
    </AddPage>
  );
}

export default function Page() {
  return <AddPage>Redirecting...</AddPage>;
}
