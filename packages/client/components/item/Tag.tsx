import classNames from 'classnames';
import Link from 'next/link';
import { useRecoilValue } from 'recoil';
import { Card, Label } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerNamespaceTag } from '../../misc/types';
import { urlstring } from '../../misc/utility';
import { AppState } from '../../state';
import Rating from '../Rating';

export type TagCardLabelData = DeepPick<
  ServerNamespaceTag,
  'id' | 'namespace.name' | 'tag.name' | 'metatags.favorite' | 'metatags.follow'
>;

export const tagCardLabelDataFields: FieldPath<ServerNamespaceTag>[] = [
  'namespace.name',
  'tag.name',
  'metatags.favorite',
  'metatags.follow',
];

export default function TagCardLabel({
  data,
  ...props
}: {
  data: TagCardLabelData;
} & React.ComponentProps<typeof Card>) {
  const appProps = useRecoilValue(AppState.properties);

  return (
    <Card
      {...props}
      basic
      className={classNames('default-card', props.className)}>
      <Card.Content>
        <Card.Header>
          <Label size="mini" className="right">
            {t`ID`}
            <Label.Detail>{data.id}</Label.Detail>
          </Label>
          <Rating
            icon="thumbtack"
            size="big"
            title={t`Follow status`}
            color="blue"
            className="right"
            defaultRating={data.metatags.follow ? 1 : 0}
          />
          <Rating
            icon="heart"
            size="big"
            color="red"
            className="right"
            defaultRating={data.metatags.favorite ? 1 : 0}
          />
          {data.namespace.name !== appProps.special_namespace && (
            <span className="sub-text">{data.namespace.name}:</span>
          )}{' '}
          {data.tag.name}
          <Link
            href={urlstring('/library', {
              q:
                data.namespace.name !== appProps.special_namespace
                  ? `${data.namespace.name}:"${data.tag.name}"`
                  : `tag:"${data.tag.name}"`,
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
        </Card.Header>
      </Card.Content>
    </Card>
  );
}
