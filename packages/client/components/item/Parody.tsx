import classNames from 'classnames';
import Link from 'next/link';
import { Card, Image, Label, Segment } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerParody } from '../../misc/types';
import { urlstring } from '../../misc/utility';
import styles from './Item.module.css';

export type ParodyCardLabelData = DeepPick<
  ServerParody,
  'id' | 'preferred_name.name'
>;

export const parodyCardLabelDataFields: FieldPath<ServerParody>[] = [
  'preferred_name.name',
];

export default function ParodyCardLabel({
  data,
  ...props
}: {
  data: ParodyCardLabelData;
} & React.ComponentProps<typeof Card>) {
  return (
    <Card
      {...props}
      basic
      className={classNames(
        styles.parody_card_label,
        'horizontal',
        'tiny-size',
        'parody',
        props.className
      )}>
      <Image
        floated="left"
        size="mini"
        src="/img/default.png"
        alt="default"
        className="parody"
      />
      <Card.Content as={Segment} color="violet">
        <Card.Header className="">{data?.preferred_name?.name}</Card.Header>
        <Card.Meta className="clearfix">
          <Label size="mini" className="right">
            {t`ID`}
            <Label.Detail>{data.id}</Label.Detail>
          </Label>
          <Link
            href={urlstring('/library', {
              q: `parody:"${data.preferred_name.name}"`,
            })}
            passHref>
            <Label
              size="small"
              empty
              icon="grid layout"
              title={t`Show galleries`}
              as="a"
            />
          </Link>
        </Card.Meta>
      </Card.Content>
    </Card>
  );
}
