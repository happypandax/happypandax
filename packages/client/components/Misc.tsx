import '@brainhubeu/react-carousel/lib/style.css';

import classNames from 'classnames';
import maxSize from 'popper-max-size-modifier';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Editor from 'react-simple-code-editor';
import { useLocalStorage, useWindowScroll } from 'react-use';
import { useRecoilState } from 'recoil';
import {
  Button,
  Divider,
  Header,
  Icon,
  Label,
  Message,
  Popup,
  Segment,
} from 'semantic-ui-react';

import Carousel, {
  arrowsPlugin,
  autoplayPlugin,
  slidesToScrollPlugin,
  slidesToShowPlugin,
} from '@brainhubeu/react-carousel';

import t from '../misc/lang';
import { parseMarkdown, scrollToTop } from '../misc/utility';
import { AppState } from '../state';
import styles from './Misc.module.css';

export function TextEditor({
  value,
  onChange,
}: {
  value?: string;
  onChange?: (value: string) => void;
}) {
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
    />
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

export function DrawerButton({ basic }: { basic?: boolean }) {
  const [open, setOpen] = useRecoilState(AppState.drawerOpen);

  return (
    <Visible visible={!open}>
      <Button
        primary
        circular
        basic={basic}
        onClick={useCallback(() => setOpen(true), [])}
        icon="window maximize outline"
        size="small"
      />
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
  as,
}: {
  title: string;
  as?: React.ElementType;
  headerSize?: React.ComponentProps<typeof Header>['size'];
  children?: React.ReactNode;
}) {
  return (
    <>
      <Header size={headerSize}>{title}</Header>
      <Segment as={as}>{children}</Segment>
    </>
  );
}

export function EmptySegment({
  title = t`Nothing to see here...`,
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <Segment placeholder disabled className="!min-0-h w-full h-full">
      <Header className="center text-center sub-text" icon>
        <Icon className="hpx-standard sub-text" size="huge" />
        {title}
        <Header.Subheader>{description}</Header.Subheader>
      </Header>
    </Segment>
  );
}

export function EmptyMessage({
  title = t`Nothing to see here...`,
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <Message>
      <Message.Header className="center text-center sub-text">
        {title}
      </Message.Header>
      <Message.Content className="text-center sub-text">
        {description}
        <Segment basic textAlign="center">
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

function SliderNav({
  direction,
  onClick,
  disabled,
}: {
  direction: 'left' | 'right';
  disabled?: boolean;
  onClick?: Function;
}) {
  return (
    <Icon
      disabled={disabled}
      name={classNames('chevron', direction)}
      onClick={onClick}
      circular
      inverted
      link
      className={classNames('slide-next', direction)}
    />
  );
}

export function Slider({
  infinite,
  children,
  label,
  color,
  autoplay,
  className,
  ...props
}: {
  infinite?: boolean;
  autoplay?: boolean;
  label?: React.ReactNode;
} & React.ComponentProps<typeof Segment>) {
  const items = React.Children.toArray(children);

  const plugins: (string | object)[] = [
    {
      resolve: arrowsPlugin,
      options: {
        arrowLeft: <SliderNav direction="left" />,
        arrowLeftDisabled: <SliderNav direction="left" disabled />,
        arrowRight: <SliderNav direction="right" />,
        arrowRightDisabled: <SliderNav direction="right" disabled />,
        addArrowClickHandler: true,
      },
    },
  ];

  if (infinite) {
    plugins.push('infinite');
  }

  if (autoplay) {
    plugins.push({
      resolve: autoplayPlugin,
      options: {
        interval: 10000,
      },
    });
  }

  return (
    <Segment basic {...props} className={classNames('slider', className)}>
      {!!label && (
        <Label color={color} attached="top">
          {label}
          <Label.Detail>{items.length}</Label.Detail>{' '}
        </Label>
      )}
      {!items.length && <EmptySegment />}
      {items && (
        <Carousel
          draggable
          plugins={plugins}
          slides={items}
          breakpoints={{
            460: {
              plugins: [
                ...plugins,
                {
                  resolve: slidesToShowPlugin,
                  options: {
                    numberOfSlides: 2,
                  },
                },
                {
                  resolve: slidesToScrollPlugin,
                  options: {
                    numberOfSlides: 1,
                  },
                },
              ],
            },
            675: {
              plugins: [
                ...plugins,
                {
                  resolve: slidesToShowPlugin,
                  options: {
                    numberOfSlides: 3,
                  },
                },
                {
                  resolve: slidesToScrollPlugin,
                  options: {
                    numberOfSlides: 2,
                  },
                },
              ],
            },
            1200: {
              plugins: [
                ...plugins,
                {
                  resolve: slidesToShowPlugin,
                  options: {
                    numberOfSlides: 5,
                  },
                },
                {
                  resolve: slidesToScrollPlugin,
                  options: {
                    numberOfSlides: 3,
                  },
                },
              ],
            },
            1800: {
              plugins: [
                ...plugins,
                {
                  resolve: slidesToShowPlugin,
                  options: {
                    numberOfSlides: 7,
                  },
                },
                {
                  resolve: slidesToScrollPlugin,
                  options: {
                    numberOfSlides: 3,
                  },
                },
              ],
            },
          }}></Carousel>
      )}
    </Segment>
  );
}

export function LabeLAccordion({
  saveKey,
  children,
  className,
  basic = true,
  label,
  detail,
  color,
  attached = 'top',
  ...props
}: {
  saveKey?: string;
  attached?: React.ComponentProps<typeof Label>['attached'];
  color?: React.ComponentProps<typeof Label>['color'];
  label?: React.ReactNode;
  detail?: React.ReactNode;
} & React.ComponentProps<typeof Segment>) {
  const key = '__labelaccordion' + (saveKey ?? '');
  const [value, setValue, remove] = useLocalStorage(key);
  const [show, setShow] = useState(value ?? true);

  return (
    <Segment
      {...props}
      basic={basic}
      className={classNames('small-padding-segment', className)}>
      <Label
        as="a"
        color={color}
        attached={attached}
        onClick={useCallback(() => {
          setShow(!show);
          if (saveKey) {
            setValue(!show);
          }
        }, [show, saveKey])}>
        <Icon name={show ? 'caret down' : 'caret right'} />
        {label}
        {!!detail && <Label.Detail>{detail}</Label.Detail>}
      </Label>
      {show && children}
      {!show && <Divider hidden fitted />}
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
