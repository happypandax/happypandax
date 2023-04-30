import { useEffect } from 'react';

import Document from '@tiptap/extension-document';
import HardBreak from '@tiptap/extension-hard-break';
import History from '@tiptap/extension-history';
import Paragraph from '@tiptap/extension-paragraph';
import Placeholder from '@tiptap/extension-placeholder';
import Text from '@tiptap/extension-text';
import { EditorContent, useEditor } from '@tiptap/react';

import t from '../../client/lang';
import styles from './MarkdownEditor.module.css';

export default function MarkdownEditor({
  content,
  onChange,
}: {
  content?: string;
  onChange?: (value: string) => void;
}) {
  const editor = useEditor({
    editorProps: {
      attributes: {
        class: `ui ${styles.editor}`,
      },
    },
    onUpdate: ({ editor }) => {
      const v = editor.getText();
      onChange?.(v);
    },
    extensions: [
      Document.extend({
        addKeyboardShortcuts() {
          return {
            Tab: () => {
              this.editor
                .chain()
                .command(({ tr }) => {
                  tr.insertText('  ');

                  return true;
                })
                .run();

              return true; // <- make sure to return true to prevent the tab from blurring.
            },
          };
        },
      }),
      Text,
      Paragraph,
      History,
      HardBreak.extend({
        addKeyboardShortcuts() {
          return {
            Enter: () => this.editor.commands.setHardBreak(),
          };
        },
      }),
      Placeholder.configure({
        placeholder: t`Markdown is supported.`,
        emptyNodeClass: styles.is_editor_empty,
      }),
    ],
    content: '',
  });

  useEffect(() => {
    if (editor && content !== undefined && content !== editor.getText()) {
      // replace all newlines with <br>

      const c = content?.replace?.(/\n/g, '<br />');

      editor.commands.setContent(c ?? '');
    }
  }, [content, editor]);

  return <EditorContent editor={editor} />;
}
