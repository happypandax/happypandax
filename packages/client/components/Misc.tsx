import { useEffect } from 'react';

import {
  enable as enableDarkMode,
  disable as disableDarkMode,
  auto as followSystemColorScheme,
} from 'darkreader';

import { parseMarkdown } from '../misc/utility';

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
      followSystemColorScheme(darkProps);
    }
  }, [name]);

  return <>{children}</>;
}
