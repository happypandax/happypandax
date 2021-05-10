import React, { useEffect, useState } from 'react';

import {
  enable as enableDarkMode,
  disable as disableDarkMode,
  auto as followSystemColorScheme,
} from 'darkreader';

export default function Theme({
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
