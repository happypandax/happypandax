import classNames from 'classnames';
import Link from 'next/link';
import { Card, Icon, Label, Segment } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerCategory } from '../../misc/types';
import { urlstring } from '../../misc/utility';

export type CategoryCardLabelData = DeepPick<ServerCategory, 'id' | 'name'>;

export const categoryCardLabelDataFields: FieldPath<ServerCategory>[] = [
  'name',
];

export default function CategoryCardLabel({
  data,
  ...props
}: {
  data: CategoryCardLabelData;
} & React.ComponentProps<typeof Card>) {
  return (
    <Card
      {...props}
      as={Segment}
      size="tiny"
      color="black"
      className={classNames('default-card', props.className)}>
      <Card.Content>
        <Label size="mini" className="right">
          {t`ID`}
          <Label.Detail>{data.id}</Label.Detail>
        </Label>
        <Link
          href={urlstring('/library', {
            q: `category:"${data.name}"`,
          })}
          passHref>
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
          <Icon name="folder" />
          {data?.name}
        </Card.Header>
      </Card.Content>
    </Card>
  );
}
