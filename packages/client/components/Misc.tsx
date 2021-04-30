import { useEffect, useState } from 'react';

import {
  enable as enableDarkMode,
  disable as disableDarkMode,
  auto as followSystemColorScheme,
} from 'darkreader';

import {
  Portal,
  Button,
  Segment,
  Header,
  Message,
  Container,
  Icon,
} from 'semantic-ui-react';

import { parseMarkdown, scrollToTop } from '../misc/utility';
import { useWindowScroll } from 'react-use';
import t from '../misc/lang';

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
