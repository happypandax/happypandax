import classNames from 'classnames';
import Link from 'next/link';
import { useRecoilValue } from 'recoil';
import { Card, Label } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ServerNamespaceTag } from '../../misc/types';
import { urlstring } from '../../misc/utility';
import { AppState } from '../../state';
import { FavoriteLabel } from '../dataview/Common';

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
  data: initialData,
  ...props
}: {
  data: TagCardLabelData;
} & React.ComponentProps<typeof Card>) {
  const appProps = useRecoilValue(AppState.properties);
  const { data, dataContext } = useSetupDataState({
    initialData,
    itemType: ItemType.NamespaceTag,
  });

  return (
    <DataContext.Provider value={dataContext}>
      <Card
        {...props}
        basic
        className={classNames('default-card', props.className)}>
        <Card.Content>
          <Card.Header>
            <FavoriteLabel
              size="big"
              defaultRating={data.metatags.favorite ? 1 : 0}
            />
            {/* <Rating
            icon="thumbtack"
            size="big"
            title={t`Follow status`}
            color="blue"
            defaultRating={data.metatags.follow ? 1 : 0}
          /> */}
            <Label size="mini" className="right">
              {t`ID`}
              <Label.Detail>{data.id}</Label.Detail>
            </Label>
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
    </DataContext.Provider>
  );
}
