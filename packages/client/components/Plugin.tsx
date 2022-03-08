import React from 'react';
import { Label, Segment } from 'semantic-ui-react';

import { PluginData } from '../misc/types';
import { LabelAccordion } from './Misc';

export function Plugin({ plugin }: { plugin: PluginData }) {
  return <Segment>test</Segment>;
}

export function PluginAccordion(props: React.ComponentProps<typeof Plugin>) {
  return (
    <LabelAccordion label={<Label>{props.plugin?.name}</Label>}>
      <Plugin {...props} />
    </LabelAccordion>
  );
}
