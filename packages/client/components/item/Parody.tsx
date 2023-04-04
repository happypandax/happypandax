import classNames from 'classnames';
import Link from 'next/link';
import { useCallback, useState } from 'react';
import { Card, Image, Label, Segment } from 'semantic-ui-react';

import t from '../../client/lang';
import { FieldPath, ServerParody } from '../../shared/types';
import { urlstring } from '../../shared/utility';
import styles from './Item.module.css';

export type ParodyCardLabelData = DeepPick<
  ServerParody,
  'id' | 'preferred_name.name' | 'profile'
>;

export const parodyCardLabelDataFields: FieldPath<ServerParody>[] = [
  'preferred_name.name',
  'profile',
];

export default function ParodyCardLabel({
  data,
  ...props
}: {
  data: ParodyCardLabelData;
} & React.ComponentProps<typeof Card>) {
  const [img, setImg] = useState(data.profile?.data);

  return (
    <Card
      {...props}
      basic
      className={classNames(
        styles.parody_card_label,
        'horizontal',
        'default-card',
        'tiny-size',
        'parody',
        props.className
      )}
    >
      <Image
        floated="left"
        size="mini"
        onError={useCallback(() => setImg('/img/default.png'), [])}
        src={img ?? '/img/default.png'}
        alt="default"
        className="parody"
      />
      <Card.Content as={Segment} size="tiny" color="violet">
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
            passHref
            legacyBehavior
          >
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
