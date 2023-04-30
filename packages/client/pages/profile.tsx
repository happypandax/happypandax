import { GetServerSidePropsResult, NextPageContext } from 'next/types';
import { useMemo, useState } from 'react';
import { Button, Header, Icon } from 'semantic-ui-react';

import { ItemActions } from '../client/actions/item';
import t from '../client/lang';
import { useQueryType } from '../client/queries';
import PageLayout from '../components/layout/Page';
import MainMenu from '../components/Menu';
import { EmptySegment, PageTitle, TitleSegment } from '../components/misc';
import { ModalWithBack } from '../components/misc/BackSupport';
import Note, { NoteForm, NoteGroup } from '../components/Note';
import { ServiceType } from '../server/constants';
import { ItemType } from '../shared/enums';
import { QueryType } from '../shared/query';
import { ServerNote } from '../shared/types';
import { useGlobalValue } from '../state/global';

import type { Server } from '../services/server';
export interface PageProps {
  notes: Unwrap<Server['items']>;
}

const noteItemsArgs = {
  item_type: ItemType.Note,
  fields: ['id', 'title', 'content', 'content_type'] as const,
  limit: 100,
};

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  const data = await server.items<ServerNote>(noteItemsArgs);

  return {
    props: {
      notes: data,
    },
  };
}

export default function Page({ notes: initialNotes }: PageProps) {
  const user = useGlobalValue('user');
  const [newNoteOpen, setNewNoteOpen] = useState(false);

  const { data: notesData, refetch: refetchNotes } = useQueryType(
    QueryType.ITEMS,
    noteItemsArgs,
    {
      initialData: initialNotes,
    }
  );

  const notes = notesData?.data;

  return (
    <PageLayout
      centered
      menu={useMemo(
        () => (
          <MainMenu></MainMenu>
        ),
        []
      )}>
      <Header as="h2" icon textAlign="center">
        <Icon name="user outline" circular />
        <Header.Content>{user?.name}</Header.Content>
      </Header>

      <PageTitle title={t`User`} />
      <TitleSegment
        icon="sticky note outline"
        titleContent={
          <span className="float-right">
            <ModalWithBack
              closeIcon
              onOpen={() => setNewNoteOpen(true)}
              onClose={() => setNewNoteOpen(false)}
              open={newNoteOpen}
              trigger={
                <Button basic primary icon="plus" size="tiny" floated="right" />
              }
              content={
                <NoteForm
                  onData={(v) => {
                    ItemActions.newItem(v, {
                      item_type: ItemType.Note,
                    }).then(() => refetchNotes());
                    setNewNoteOpen(false);
                  }}
                />
              }
            />
          </span>
        }
        title={<Header.Content>{t`Notes`}</Header.Content>}>
        {!notes?.items?.length && <EmptySegment />}
        <NoteGroup>
          {notes?.items
            ?.sort?.((a: ServerNote, b: ServerNote) => {
              // sort by title
              if (a.title < b.title) {
                return -1;
              }
              if (a.title > b.title) {
                return 1;
              }
              return 0;
            })
            ?.map?.((note: ServerNote) => (
              <Note
                data={note}
                key={note.id}
                onUpdated={() => refetchNotes()}
              />
            ))}
        </NoteGroup>
      </TitleSegment>
      <TitleSegment icon="bar chart" title={t`Statistics`}>
        <EmptySegment />
      </TitleSegment>
    </PageLayout>
  );
}
