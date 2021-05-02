import React, { useEffect, useState } from 'react';

import {
  enable as enableDarkMode,
  disable as disableDarkMode,
  auto as followSystemColorScheme,
} from 'darkreader';
import Carousel, {
  slidesToShowPlugin,
  arrowsPlugin,
  autoplayPlugin,
  slidesToScrollPlugin,
} from '@brainhubeu/react-carousel';
import '@brainhubeu/react-carousel/lib/style.css';

import {
  Portal,
  Button,
  Segment,
  Label,
  Header,
  Accordion,
  Message,
  Container,
  Icon,
} from 'semantic-ui-react';

import { parseMarkdown, scrollToTop } from '../misc/utility';
import { useLocalStorage, useWindowScroll } from 'react-use';
import t from '../misc/lang';
import classNames from 'classnames';
import { useCallback } from 'react';
import { Divider } from 'semantic-ui-react';

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

export function Theme({
  name,
  children,
}: {
  name?: 'light' | 'dark';
  children: React.ReactNode | React.ReactNode[];
}) {
  return children;
  useEffect(() => {
    const darkProps = {
      brightness: 100,
      contrast: 70,
      sepia: 5,
    };

    if (name) {
      followSystemColorScheme(false);
      if (name === 'dark') {
        enableDarkMode(darkProps);
      } else {
        disableDarkMode();
      }
    } else {
      // followSystemColorScheme(darkProps);
    }
  }, [name]);

  return <>{children}</>;
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
}) {
  return visible ? children : null;
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
    <Segment placeholder disabled className="!min-0-h">
      <Header className="center text-center sub-text" icon>
        <Icon className="grin beam sweat outline sub-text" size="huge" />
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
          <Icon className="grin beam sweat outline sub-text" size="huge" />
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
      {!show && <Divider hidden />}
    </Segment>
  );
}
