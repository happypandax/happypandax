import classNames from 'classnames';
import Link from 'next/link';
import { useCallback, useState } from 'react';
import {
  Card,
  Checkbox,
  Grid,
  Header,
  Icon,
  Label,
  List,
  Segment,
} from 'semantic-ui-react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import { MutatationType, useMutationType } from '../../client/queries';
import { getLibraryQuery } from '../../client/utility';
import { ViewType } from '../../shared/enums';
import { FieldPath, ServerFilter } from '../../shared/types';
import { urlstring } from '../../shared/utility';
import { LabelAccordion } from '../misc';

export type FilterCardData = DeepPick<
  ServerFilter,
  | 'id'
  | 'name'
  | 'info'
  | 'filter'
  | 'enforce'
  | 'search_options'
  | 'gallery_count'
>;

export const filterCardDataFields: FieldPath<ServerFilter>[] = [
  'name',
  'info',
  'filter',
  'enforce',
  'search_options',
  'gallery_count',
];

export default function FilterCard({
  data,
  ...props
}: { data: FilterCardData } & React.ComponentProps<typeof Card>) {
  const [updating, setUpdating] = useState(false);

  const { mutate, data: filterUpdateData } = useMutationType(
    MutatationType.UPDATE_FILTERS,
    {
      onMutate: () => setUpdating(true),
    }
  );

  useCommand(filterUpdateData ? filterUpdateData.data : undefined, {}, () => {
    setUpdating(false);
  });

  return (
    <Card
      color="black"
      {...props}
      className={classNames('horizontal', 'default-card', props.className)}>
      <Card.Content>
        <Card.Header>
          {data.name}{' '}
          <Label size="mini" basic>
            {data?.gallery_count}
          </Label>
          <Label size="mini" className="right">
            {t`ID`}
            <Label.Detail>{data.id}</Label.Detail>
          </Label>
        </Card.Header>
        <Card.Meta>{data.info || t`No description`}</Card.Meta>
        <Card.Meta className="clearfix">
          <Label
            size="small"
            className="right"
            empty
            color={updating ? 'orange' : undefined}
            icon={<Icon name="refresh" loading={updating} />}
            onClick={useCallback(() => {
              if (data) mutate({ item_ids: [data?.id] });
            }, [data])}
            title={t`Update`}
            as="a"
          />
          <Link
            href={urlstring('/library', {
              ...getLibraryQuery({
                query: '',
                view: ViewType.All,
                favorites: false,
                filter: data.id,
              }),
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
        </Card.Meta>
        {!!data.filter && (
          <LabelAccordion noPadding basicLabel color="blue" label={t`Filter`}>
            <Segment
              basic
              tertiary
              className="no-margins medium-padding-segment">
              {data.filter}
            </Segment>
          </LabelAccordion>
        )}
        <LabelAccordion noPadding label={t`Options`}>
          <Grid columns="equal">
            <Grid.Row>
              <Grid.Column>
                <List divided>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.enforce}
                      toggle
                      label={t`Enforce`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.case_sensitive'
                      )}
                      toggle
                      label={t`Case sensitive`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.match_all_terms'
                      )}
                      toggle
                      label={t`Match all terms`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.match_exact'
                      )}
                      toggle
                      label={t`Match terms exactly`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.children'
                      )}
                      toggle
                      label={t`Match on children`}
                    />
                  </List.Item>
                  <List.Item>
                    <Checkbox
                      defaultChecked={data.search_options.includes(
                        'search.regex'
                      )}
                      toggle
                      label={t`Regex`}
                    />
                  </List.Item>
                </List>
              </Grid.Column>
              <Grid.Column>
                {!!data.filter && (
                  <Card.Description
                    as={Segment}
                    tertiary
                    className={classNames('small-padding-segment')}>
                    {data.filter}
                  </Card.Description>
                )}
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </LabelAccordion>
      </Card.Content>
    </Card>
  );
}
