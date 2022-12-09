import classNames from 'classnames';
import Link from 'next/link';
import { Card, Icon, Label, Segment } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerLanguage } from '../../misc/types';
import { urlstring } from '../../misc/utility';

export type LanguageCardLabelData = DeepPick<ServerLanguage, 'id' | 'name'>;

export const languageCardLabelDataFields: FieldPath<ServerLanguage>[] = [
  'name',
];

export default function LanguageCardLabel({
  data,
  ...props
}: {
  data: LanguageCardLabelData;
} & React.ComponentProps<typeof Card>) {
  return (
    <Card
      {...props}
      as={Segment}
      size="tiny"
      color="blue"
      className={classNames('default-card', props.className)}>
      <Card.Content>
        <Label size="mini" className="right">
          {t`ID`}
          <Label.Detail>{data.id}</Label.Detail>
        </Label>
        <Link
          href={urlstring('/library', {
            q: `language:"${data.name}"`,
          })}
          passHref
          legacyBehavior>
          <Label
            size="small"
            empty
            className="right"
            icon="grid layout"
            title={t`Show galleries`}
            as="a"
          />
        </Link>
        <Card.Header>
          <Icon className="globe africa" />
          {data?.name}
        </Card.Header>
      </Card.Content>
    </Card>
  );
}
