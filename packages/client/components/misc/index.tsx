import '@brainhubeu/react-carousel/lib/style.css';

import classNames from 'classnames';
import maxSize from 'popper-max-size-modifier';
import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from 'react';
import { useDrop } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
import Editor from 'react-simple-code-editor';
import { useUpdateEffect, useWindowScroll } from 'react-use';
import {
  Button,
  Confirm as SemanticConfirm,
  Dimmer,
  Divider,
  Header,
  Icon,
  Label,
  List,
  Message,
  Popup,
  Ref,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { parseMarkdown, scrollToTop } from '../../client/utility';
import { LogType } from '../../shared/enums';
import { FileT } from '../../shared/types';
import { humanFileSize } from '../../shared/utility';
import { MiscState } from '../../state';
import { useInitialRecoilState } from '../../state/index';
import styles from './Misc.module.css';

export function Confirm(props: React.ComponentProps<typeof SemanticConfirm>) {
  return (
    <SemanticConfirm
      cancelButton={t`Cancel`}
      confirmButton={t`Confirm`}
      {...props}
    />
  );
}

export function ServerLog({
  type,
  ...props
}: React.ComponentProps<typeof Segment> & { type: LogType }) {
  const { data, isLoading } = useQueryType(
    QueryType.LOG,
    { log_type: type },
    { refetchInterval: 2000, keepPreviousData: true }
  );

  return (
    <Segment
      className="max-300-h overflow-auto"
      loading={isLoading}
      secondary
      {...props}>
      <pre>{data?.data?.log}</pre>
    </Segment>
  );
}

export function TextEditor({
  onChange,
  value,
  ...props
}: {
  value?: string;
  onChange?: (value: string) => void;
} & Omit<
  React.ComponentProps<typeof Editor>,
  'ref' | 'onValueChange' | 'onChange' | 'highlight' | 'value'
>) {
  return (
    <Editor
      value={value}
      onValueChange={onChange}
      highlight={(s) => s}
      padding={10}
      style={{
        border: '1px solid rgba(34, 36, 38, 0.15)',
        background: 'rgba(0, 0, 0, 0.05) none repeat scroll 0% 0%',
        minHeight: '8em',
      }}
      placeholder="</ Text here ...>"
      {...props}
    />
  );
}

export function JSONTextEditor({
  value,
  defaultValue,
  onChange: initialOnChange,
  pretty,
  ...props
}: {
  value?: object;
  defaultValue?: object;
  pretty?: boolean;
  onChange?: (value: object) => void;
} & Omit<
  React.ComponentProps<typeof TextEditor>,
  'value' | 'onChange' | 'defaultValue'
>) {
  const [error, setError] = useState('');
  const [textValue, setTextValue] = useState<string>(
    value ? JSON.stringify(value, undefined, pretty ? 2 : undefined) : undefined
  );

  const onChange = useCallback(
    (v: string) => {
      try {
        const o = JSON.parse(v.trim());
        initialOnChange?.(o);
        setError('');
      } catch (e) {
        setError(e.message);
      }
      if (textValue !== undefined) {
        setTextValue(v);
      }
    },
    [initialOnChange]
  );

  useEffect(() => {
    if (value !== undefined) {
      setTextValue(JSON.stringify(value, undefined, pretty ? 2 : undefined));
    }
  }, [value]);

  return (
    <div>
      <TextEditor
        {...props}
        value={textValue}
        defaultValue={
          defaultValue
            ? JSON.stringify(defaultValue, undefined, pretty ? 2 : undefined)
            : undefined
        }
        onChange={onChange}
      />
      {!!error && (
        <Message negative>
          <p>{error}</p>
        </Message>
      )}
    </div>
  );
}

export function PageTitle({ title }: { title?: string }) {
  if (!global.app.IS_SERVER) {
    document.title = title
      ? title + ' - ' + global.app.title
      : global.app.title;
  }
  return null;
}

export function Markdown({ children }: { children?: string }) {
  return <div dangerouslySetInnerHTML={{ __html: parseMarkdown(children) }} />;
}

export function ScrollUpButton() {
  const { y } = useWindowScroll();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (y > 300) {
      if (!visible) {
        setVisible(true);
      }
    } else {
      if (visible) {
        setVisible(false);
      }
    }
  }, [y, visible]);

  return (
    <Visible visible={visible}>
      <Button onClick={scrollToTop} icon="chevron up" size="small" basic />
    </Visible>
  );
}

export function Visible({
  children,
  visible,
}: {
  children: React.ReactNode;
  visible?: boolean;
}): JSX.Element {
  return visible ? (children as any) : null;
}

export function TitleSegment({
  title,
  headerSize,
  children,
  titleContent,
  icon,
  as,
}: {
  title: string | React.ReactNode;
  icon?: React.ComponentProps<typeof Icon>['name'];
  as?: React.ElementType;
  headerSize?: React.ComponentProps<typeof Header>['size'];
  children?: React.ReactNode;
  titleContent?: React.ReactNode;
}) {
  return (
    <>
      <Header size={headerSize}>
        {titleContent}
        {!!icon && <Icon name={icon} />}
        {title}
      </Header>
      <Segment as={as}>{children}</Segment>
    </>
  );
}

export function EmptySegment({
  title = t`Nothing to see here...`,
  description,
  fluid = true,
  children,
}: {
  title?: React.ReactNode;
  children?: React.ReactNode;
  fluid?: boolean;
  description?: React.ReactNode;
}) {
  return (
    <Segment
      placeholder
      disabled
      className={classNames('!min-0-h w-full', { 'h-full': fluid })}>
      <Header className="center text-center sub-text" icon>
        <Icon className="hpx-standard sub-text" size="huge" />
        {title}
        <Header.Subheader>{description}</Header.Subheader>
      </Header>
      {children}
    </Segment>
  );
}

export function EmptyMessage({
  title = t`Nothing to see here...`,
  description,
  className,
  loading,
}: {
  title?: string;
  loading?: boolean;
  className?: React.ReactNode;
  description?: React.ReactNode;
}) {
  return (
    <Message className={className}>
      <Message.Header className="center text-center sub-text">
        {title}
      </Message.Header>
      <Message.Content className="text-center sub-text">
        {description}
        <Segment basic textAlign="center" loading={loading}>
          <Icon className="hpx-standard sub-text" size="huge" />
        </Segment>
      </Message.Content>
    </Message>
  );
}

// export function Slider({
//   autoPlay,
//   children,
//   className,
//   ...props
// }: {
//   autoPlay?: boolean;
// } & React.ComponentProps<typeof Segment>) {
//   const items = React.Children.toArray(children);
//   return (
//     <Segment basic {...props} className={classNames('slider', className)}>
//       {!items.length && <EmptySegment />}
//       {items && (
//         <Carousel
//           autoPlay={autoPlay ?? false}
//           showThumbs={false}
//           showStatus={false}
//           centerMode
//           centerSlidePercentage={50}
//           emulateTouch
//           interval={10000}>
//           {children}
//         </Carousel>
//       )}
//     </Segment>
//   );
// }

export function LabelAccordion({
  stateKey,
  children,
  className,
  basic = true,
  basicLabel,
  label,
  detail,
  visible: initialVisible,
  defaultVisible,
  onVisible,
  color,
  segmentColor,
  attached = 'top',
  noPadding,
  ...props
}: {
  stateKey?: string;
  visible?: boolean;
  noPadding?: boolean;
  segmentColor?: SemanticCOLORS;
  basicLabel?: boolean;
  defaultVisible?: boolean;
  onVisible?: (show: boolean) => void;
  attached?: React.ComponentProps<typeof Label>['attached'];
  color?: React.ComponentProps<typeof Label>['color'];
  label?: React.ReactNode;
  detail?: React.ReactNode;
} & React.ComponentProps<typeof Segment>) {
  const [show, setVisible] = stateKey
    ? // eslint-disable-next-line react-hooks/rules-of-hooks
      useInitialRecoilState(
        MiscState.labelAccordionOpen(stateKey),
        initialVisible ?? defaultVisible
      )
    : // eslint-disable-next-line react-hooks/rules-of-hooks
      useState(initialVisible ?? defaultVisible);

  const visible = initialVisible ?? show;

  useUpdateEffect(() => {
    onVisible?.(visible);
  }, [visible]);

  return (
    <Segment
      {...props}
      color={segmentColor}
      basic={basic}
      className={classNames(
        {
          ['small-padding-segment']: !noPadding,
          ['no-padding-segment']: noPadding,
        },
        className
      )}>
      <Label
        as="a"
        color={color}
        basic={basicLabel}
        attached={attached}
        onClick={useCallback(
          (e) => {
            e.preventDefault();
            if (initialVisible === undefined) {
              setVisible(!visible);
            }
          },
          [visible]
        )}>
        <Icon name={visible ? 'caret down' : 'caret right'} />
        {label}
        {!!detail && <Label.Detail>{detail}</Label.Detail>}
      </Label>
      {visible && children}
      {!visible && <Divider hidden fitted />}
    </Segment>
  );
}

export function PageInfoMessage({
  props,
  className,
  color,
  hidden,
  size,
  onDismiss,
  children,
}: React.ComponentProps<typeof Message>) {
  return (
    <Message
      hidden={hidden}
      color={color}
      onDismiss={onDismiss}
      size={size}
      className={classNames(styles.pageinfo_message, className)}
      {...props}>
      {children}
    </Message>
  );
}

export function PopupNoOverflow(props: React.ComponentProps<typeof Popup>) {
  const applyMaxSize = useMemo(() => {
    return {
      name: 'applyMaxSize',
      enabled: true,
      phase: 'beforeWrite',
      requires: ['maxSize'],
      fn({ state }) {
        // The `maxSize` modifier provides this data
        const { width, height } = state.modifiersData.maxSize;

        state.styles.popper = {
          ...state.styles.popper,
          maxWidth: `${Math.max(100, width)}px`,
          maxHeight: `${Math.max(100, height)}px`,
        };
      },
    };
  }, []);

  return (
    <Popup
      {...props}
      offset={[20, 0]}
      popperModifiers={[maxSize, applyMaxSize]}
    />
  );
}

export function FileDropZone({
  onFiles,
  files = [],
  ...props
}: {
  files?: FileT[];
  onFiles: (files: FileT[]) => void;
} & React.ComponentProps<typeof Segment>) {
  const [droppedFiles, setDroppedFiles] = useState<FileT[]>(files);

  const [{ canDrop, isOver }, drop] = useDrop(
    () => ({
      accept: [NativeTypes.FILE],
      drop(item: DataTransfer) {
        if (item) {
          const files = item.items;
          setDroppedFiles([
            ...droppedFiles,
            ...Array.from(files).map((f) => {
              const o: FileT = f.getAsFile();
              o.isDirectory = f.webkitGetAsEntry().isDirectory;
              return o;
            }),
          ]);
        }
      },
      canDrop(item: any) {
        return true;
      },
      collect: (monitor) => {
        return {
          isOver: monitor.isOver(),
          canDrop: monitor.canDrop(),
        };
      },
    }),
    [droppedFiles]
  );

  useUpdateEffect(() => {
    onFiles?.(droppedFiles);
  }, [droppedFiles]);

  useEffect(() => {
    setDroppedFiles(files);
  }, [files]);

  const dropEl = (
    <Header
      inverted={!!droppedFiles.length}
      className="center text-center sub-text"
      icon>
      <Icon
        color={isOver ? 'green' : undefined}
        className="hpx-standard sub-text"
        size="huge"
      />
      {isOver ? t`Release!` : t`Drop files here`}
    </Header>
  );

  let el = dropEl;

  if (droppedFiles.length) {
    el = (
      <>
        <Dimmer active={isOver}>{dropEl}</Dimmer>
        <List divided verticalAlign="middle">
          {droppedFiles.map((file, idx) => {
            return (
              <List.Item key={file.name}>
                <List.Icon name={file.isDirectory ? 'folder' : 'file'} />
                <List.Content>
                  <List.Header>
                    {file.name}

                    <Button
                      floated="right"
                      icon="remove"
                      size="mini"
                      color="red"
                      onClick={() =>
                        setDroppedFiles(
                          droppedFiles.filter((_, i) => i !== idx)
                        )
                      }
                    />
                  </List.Header>
                  <List.Description>
                    {file.isDirectory ? t`Folder` : humanFileSize(file.size)}
                  </List.Description>
                </List.Content>
              </List.Item>
            );
          })}
        </List>
      </>
    );
  }

  return (
    <Ref innerRef={drop}>
      <Segment
        {...props}
        placeholder={!droppedFiles.length}
        tertiary={!droppedFiles.length}
        className="min-200-h">
        {el}
      </Segment>
    </Ref>
  );
}

export function NoSSR({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useLayoutEffect(() => {
    setMounted(true);
  }, []);
  return mounted ? <>{children}</> : null;
}
