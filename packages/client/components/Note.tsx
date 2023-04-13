import { useCallback, useEffect, useState } from 'react';
import { Card, Form, Header, Icon, Modal, Segment } from 'semantic-ui-react';

import { ItemActions } from '../client/actions/item';
import t from '../client/lang';
import { ItemType } from '../shared/enums';
import { ServerNote } from '../shared/types';
import { Markdown } from './misc';
import { ModalWithBack } from './misc/BackSupport';
import MarkdownEditor from './misc/MarkdownEditor';

export function NoteForm({
  data,
  onData,
}: {
  data?: Partial<ServerNote>;
  onData?: (data: Partial<ServerNote>) => void;
}) {
  const [formData, setFormData] = useState<Partial<ServerNote>>(data ?? {});

  const onSubmit = useCallback(
    (e) => {
      e.preventDefault();
      onData?.(formData);
    },
    [formData]
  );

  return (
    <Segment basic>
      <Header>{data ? t`Edit note` : t`Create new note`}</Header>
      <Form onSubmit={onSubmit}>
        <Form.Input
          fluid
          label={t`Title`}
          placeholder={t`Title`}
          value={formData?.title ?? ''}
          onChange={(e) => {
            setFormData({ ...formData, title: e.target.value });
          }}
        />
        <Form.Field>
          <label>{t`Content`}</label>
          <MarkdownEditor
            content={formData?.content ?? ''}
            onChange={(v) => {
              setFormData({ ...formData, content: v });
            }}
          />
        </Form.Field>
        <Form.Button primary type="submit">
          Submit
        </Form.Button>
      </Form>
    </Segment>
  );
}

export default function Note({
  data: initalData,
  onUpdated,
}: {
  data?: Partial<ServerNote>;
  onUpdated?: (data: Partial<ServerNote>) => void;
}) {
  const [open, setOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [data, setData] = useState(initalData ?? {});

  useEffect(() => {
    setData(initalData ?? {});
  }, [initalData]);

  let content = data?.content ?? '';

  if (content.length > 100) {
    // cut off at 200 characters and add ellipsis
    content = content.slice(0, 200) + '...';
  }

  return (
    <>
      <ModalWithBack
        closeIcon
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}>
        <Modal.Header>{data?.title}</Modal.Header>
        <Modal.Content>
          <Markdown>{data?.content}</Markdown>
        </Modal.Content>
      </ModalWithBack>
      <ModalWithBack
        open={editOpen}
        onOpen={() => setEditOpen(true)}
        onClose={() => setEditOpen(false)}
        closeIcon
        content={
          <NoteForm
            data={data}
            onData={(v) => {
              ItemActions.updateItem(data?.id, v, {
                item_type: ItemType.Note,
                item: v,
              }).then(() => onUpdated?.(v));
              setEditOpen(false);
            }}
          />
        }
      />
      <Card
        onClick={(e) => {
          e.preventDefault();
          setOpen(true);
        }}>
        <Card.Content>
          <Card.Header>
            {data?.title}
            <Icon
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setEditOpen(true);
              }}
              name="pencil"
              link
              size="small"
              className="float-right"
            />
          </Card.Header>
          {/* <Card.Meta>Friends of Elliot</Card.Meta> */}
          <Card.Description>
            <span
              style={{
                whiteSpace: 'pre-wrap',
              }}>
              {content}
            </span>
          </Card.Description>
        </Card.Content>
      </Card>
    </>
  );
}

export function NoteGroup(props: React.ComponentProps<typeof Card.Group>) {
  return <Card.Group {...props} />;
}
