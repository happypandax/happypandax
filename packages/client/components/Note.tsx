import { useCallback, useEffect, useState } from 'react';
import { Card, Form, Header, Icon, Modal } from 'semantic-ui-react';

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
  onCancel,
}: {
  data?: Partial<ServerNote>;
  onData?: (data: Partial<ServerNote>) => void;
  onCancel?: () => void;
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
      <Form.Group>
        <Form.Button primary type="submit">
          {t`Submit`}
        </Form.Button>
        <Form.Button onClick={onCancel} type="button">{t`Cancel`}</Form.Button>
      </Form.Group>
    </Form>
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
  const [edit, setEdit] = useState(false);
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
        <Modal.Header>
          {edit ? t`Edit note` : data?.title}
          <Icon
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setEdit(true);
            }}
            name="pencil"
            link
            size="small"
            className="float-right"
          />
        </Modal.Header>
        <Modal.Content>
          {edit && (
            <NoteForm
              data={data}
              onCancel={() => setEdit(false)}
              onData={(v) => {
                ItemActions.updateItem(data?.id, v, {
                  item_type: ItemType.Note,
                  item: v,
                }).then(() => onUpdated?.(v));
                setEdit(false);
              }}
            />
          )}
          {!edit && <Markdown>{data?.content}</Markdown>}
        </Modal.Content>
      </ModalWithBack>
      <Card
        onClick={(e) => {
          e.preventDefault();
          setOpen(true);
        }}>
        <Card.Content>
          <Card.Header>{data?.title}</Card.Header>
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
