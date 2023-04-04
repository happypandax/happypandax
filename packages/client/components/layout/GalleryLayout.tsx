import classNames from 'classnames';
import Link from 'next/link';
import React, { useCallback, useMemo } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import {
  Button,
  ButtonGroup,
  Container,
  Divider,
  Dropdown,
  Grid,
  Header,
  Icon,
  Image,
  Label,
  Menu,
  Popup,
  Segment,
} from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useImage, useSetupDataState } from '../../client/hooks/item';
import { useBreakpoints } from '../../client/hooks/ui';
import t, { sortIndexName } from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemSort, ItemType, ViewType } from '../../shared/enums';
import {
  FieldPath,
  ServerFilter,
  ServerGallery,
  ServerSortIndex,
} from '../../shared/types';
import { urlstring } from '../../shared/utility';
import { AppState } from '../../state';
import { useGlobalValue } from '../../state/global';
import {
  ArtistLabels,
  CategoryLabel,
  CircleLabels,
  DateAddedLabel,
  DatePublishedLabel,
  FavoriteLabel,
  GroupingLabel,
  InfoSegment,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  NamesTable,
  ParodyLabels,
  RatingLabel,
  StatusLabel,
  TagsTable,
  UrlList,
} from '../dataview/Common';
import { ContinueButton, GalleryMenu } from '../item/Gallery';
import { PopupNoOverflow } from '../misc';
import { ItemHeaderParallax, LabelField, LabelFields } from './ItemLayout';
import styles from './ItemLayout.module.css';

export function SortButtonInput({
  itemType,
  className,
  data: initialData,
  active,
  setActive,
}: {
  itemType: ItemType;
  className?: string;
  active?: number;
  data?: ServerSortIndex[];
  setActive: (f: number) => void;
}) {
  const { data } = useQueryType(
    QueryType.SORT_INDEXES,
    {
      item_type: itemType,
      translate: false,
      children: true,
    },
    {
      initialData,
      select: (data) => {
        data.data = data.data.filter((x) => {
          // prefer Grouping's date
          if (
            x.item_type === ItemType.Grouping &&
            x.index === ItemSort.GalleryDate
          ) {
            return false;
          }

          // prefer Grouping's random
          if (
            x.item_type === ItemType.Grouping &&
            x.index === ItemSort.GalleryRandom
          ) {
            return false;
          }

          return true;
        });
        return data;
      },
    }
  );

  return (
    <PopupNoOverflow
      on="click"
      position="left center"
      hoverable
      eventsEnabled
      positionFixed
      flowing
      wide
      className={classNames('overflow-y-auto', 'overflow-x-hidden')}
      popperDependencies={[data]}
      trigger={
        <Button
          icon="sort alphabet down"
          primary
          circular
          className={classNames(className)}
        />
      }
    >
      <Popup.Content>
        <Menu secondary vertical>
          {!!data?.data &&
            data.data
              .sort((a, b) =>
                sortIndexName[a.index]?.localeCompare(sortIndexName[b.index])
              )
              .map((v) => (
                <Menu.Item
                  key={v.index}
                  index={v.index}
                  active={v.index === active}
                  icon="sort"
                  color="blue"
                  name={sortIndexName[v.index]}
                  onClick={() => {
                    setActive(v.index);
                  }}
                />
              ))}
        </Menu>
      </Popup.Content>
    </PopupNoOverflow>
  );
}

export function SortOrderButton(
  props: React.ComponentProps<typeof Button> & { descending?: boolean }
) {
  return (
    <Button
      icon={{
        className: props.descending
          ? 'sort amount down'
          : 'sort amount down alternate',
      }}
      primary
      circular
      basic
      color="blue"
      title={props.descending ? t`Descending order` : t`Ascending order`}
      {...props}
    />
  );
}

export function ClearFilterButton(props: React.ComponentProps<typeof Button>) {
  return (
    <Button
      icon="close"
      primary
      circular
      basic
      color="red"
      title={t`Clear filter`}
      {...props}
    />
  );
}

export function FilterButtonInput({
  className,
  active,
  data: initialData,
  setActive,
}: {
  className?: string;
  active: number;
  setActive: (f: number) => void;
  data?: ServerFilter[];
}) {
  const { data } = useQueryType(
    QueryType.ITEMS,
    {
      item_type: ItemType.Filter,
      fields: ['name'] as FieldPath<ServerFilter>[],
      limit: 9999, // no limit
    },
    {
      initialData: initialData
        ? {
            count: initialData.length,
            items: initialData,
          }
        : undefined,
    }
  );

  return (
    <PopupNoOverflow
      on="click"
      position="left center"
      hoverable
      wide
      flowing
      positionFixed
      className={classNames('overflow-y-auto', 'overflow-x-hidden')}
      eventsEnabled
      popperDependencies={[data]}
      trigger={
        <Button
          icon="filter"
          primary
          inverted={!!!active}
          circular
          className={classNames(className)}
        />
      }
    >
      <Popup.Content>
        <Menu secondary vertical>
          {!!data?.data &&
            data.data?.items
              ?.sort((a, b) => a.name.localeCompare(b.name))
              .map?.((v) => (
                <Menu.Item
                  key={v.id}
                  index={v.id}
                  active={active === v.id}
                  icon="filter"
                  color="blue"
                  name={v.name}
                  onClick={() => {
                    setActive(v.id);
                  }}
                />
              ))}
        </Menu>
      </Popup.Content>
    </PopupNoOverflow>
  );
}

export function OnlyFavoritesButton({
  className,
  active,
  setActive,
}: {
  className?: string;
  active: boolean;
  setActive: (boolean) => void;
}) {
  return (
    <Button
      icon="heart"
      title={t`Show only favorites`}
      basic={!active}
      color="red"
      onClick={useCallback(() => {
        setActive(!active);
      }, [active])}
      circular
      className={classNames(className)}
    />
  );
}

export function ViewButtons({
  size = 'small',
  item,
  onView,
  onItem,
  hideItems,
  view,
}: {
  size?: React.ComponentProps<typeof ButtonGroup>['size'];
  view: ViewType;
  hideItems?: boolean;
  onView: (view: ViewType) => void;
  item: ItemType;
  onItem: (item: ItemType) => void;
}) {
  const options = useMemo(
    () => [
      {
        text: (
          <>
            <Icon name="th" /> {t`All`}
          </>
        ),
        value: ViewType.All,
      },
      {
        text: (
          <>
            <Icon name="archive" /> {t`Library`}
          </>
        ),
        value: ViewType.Library,
      },
      {
        text: (
          <>
            <Icon name="inbox" /> {t`Inbox`}
          </>
        ),
        value: ViewType.Inbox,
      },
    ],
    []
  );

  const onCollection = useCallback(() => {
    onItem?.(ItemType.Collection);
  }, []);

  const onGallery = useCallback(() => {
    onItem?.(ItemType.Gallery);
  }, []);

  return (
    <ButtonGroup toggle basic size={size}>
      <Dropdown
        selectOnBlur={false}
        disabled={view === ViewType.Favorite}
        basic
        className="active"
        value={view}
        onChange={useCallback((ev, data) => {
          ev.preventDefault();
          onView?.(data.value as ViewType);
        }, [])}
        options={options}
        button
      />
      {!hideItems && (
        <>
          <Button
            primary
            basic={item === ItemType.Collection}
            onClick={onCollection}
          >{t`Collection`}</Button>
          <Button
            primary
            basic={item === ItemType.Gallery}
            onClick={onGallery}
          >{t`Gallery`}</Button>
        </>
      )}
    </ButtonGroup>
  );
}

export type GalleryHeaderData = DeepPick<
  ServerGallery,
  | 'id'
  | 'preferred_title.name'
  | 'artists.[].id'
  | 'artists.[].preferred_name.name'
  | 'profile'
  | 'number'
  | 'rating'
  | 'info'
  | 'metatags.favorite'
  | 'metatags.read'
  | 'metatags.inbox'
  | 'progress.end'
  | 'progress.page.number'
  | 'progress.percent'
  | 'language.code'
  | 'language.name'
  | 'last_read'
  | 'times_read'
  | 'page_count'
  | 'grouping.status.name'
  | 'last_updated'
  | 'timestamp'
>;

export const galleryHeaderDataFields: FieldPath<ServerGallery>[] = [
  'artists.names.name',
  'artists.circles.name',
  'artists.preferred_name.name',
  'parodies.names.name',
  'parodies.preferred_name.name',
  'preferred_title.name',
  'preferred_title.language.name',
  'titles.name',
  'titles.language.name',
  'language.name',
  'grouping.name',
  'grouping.status.name',
  'tags.namespace.name',
  'tags.tag.name',
  'category.name',
  'urls.name',
  'times_read',
  'info',
  'page_count',
  'circles.name',
  'profile',
  'rating',
  'number',
  'language.code',
  'progress.end',
  'progress.page.number',
  'progress.percent',
  'metatags.*',
  'last_read',
  'last_updated',
  'timestamp',
  'pub_date',
];

export function GalleryItemHeader({
  data: initialData,
}: {
  data: GalleryHeaderData;
}) {
  const { isMobileMax, isTabletMin } = useBreakpoints();
  const blur = useRecoilValue(AppState.blur);
  const [readingQueue, setReadingQueue] = useRecoilState(AppState.readingQueue);

  const sameMachine = useGlobalValue('sameMachine');

  const { data, dataContext } = useSetupDataState({
    initialData,
    itemType: ItemType.Gallery,
    key: 'header',
  });

  const { src } = useImage(data?.profile);

  const hasProgress = !!data?.progress && !data?.progress?.end;

  const inReadingQueue = readingQueue?.includes?.(data?.id);

  const namesTableEl = (
    <NamesTable dataKey="titles" dataPrimaryKey="preferred_title">
      <FavoriteLabel
        defaultRating={data?.metatags?.favorite ? 1 : 0}
        size="gigantic"
        className="float-left"
      />
      <GalleryMenu
        hasProgress={hasProgress}
        read={data?.metatags?.read}
        trigger={
          <Icon
            link
            size="large"
            className="float-right"
            name="ellipsis vertical"
          />
        }
      />
    </NamesTable>
  );

  const detailsSegment = (
    <Segment
      className={classNames('no-margins', {
        'no-right-padding': !isMobileMax,
        'no-padding-segment': isMobileMax,
      })}
      basic
    >
      {isTabletMin && namesTableEl}
      <Header textAlign="center">
        <LastReadLabel timestamp={data?.last_read} />
        <LastUpdatedLabel timestamp={data?.last_updated} />
        <DateAddedLabel timestamp={data?.timestamp} />
      </Header>
      {data?.info && <InfoSegment fluid />}
      <Divider hidden className="small" />
      <LabelFields>
        <LabelField label={t`Series`} padded={false}>
          <Label.Group>
            <GroupingLabel />
            <StatusLabel>{data?.grouping?.status?.name}</StatusLabel>
          </Label.Group>
        </LabelField>
        <LabelField label={t`Parody`} padded={false}>
          <ParodyLabels />
        </LabelField>
        <LabelField label={t`Tags`} padded={false}>
          <TagsTable />
        </LabelField>
        <LabelField label={t`External links`} padded={false}>
          <UrlList />
        </LabelField>
      </LabelFields>
    </Segment>
  );

  return (
    <>
      <ItemHeaderParallax data={data} />
      <DataContext.Provider value={dataContext}>
        <Container>
          <Segment basic className="no-margins no-top-padding no-right-padding">
            <div className={classNames(styles.header_content)}>
              <div
                className={classNames(styles.cover_column, {
                  [styles.fluid]: isMobileMax,
                })}
              >
                <Image
                  centered
                  rounded
                  className={classNames({ blur: blur }, styles.cover_hero)}
                  alt="cover image"
                  id={styles.cover}
                  src={src}
                  width={data?.profile?.size?.[0]}
                  height={data?.profile?.size?.[1]}
                />
                <Divider hidden />

                <Divider fitted horizontal>
                  <Header as="h5">
                    <Button size="mini" basic>
                      <Icon name="cogs" /> {t`Configuration`}
                    </Button>
                    <Button size="mini" basic>
                      <Icon name="file alternate" /> {t`Log`}
                    </Button>
                  </Header>
                </Divider>
                {isMobileMax && namesTableEl}
                <Divider hidden />
                <Grid>
                  {hasProgress && (
                    <Grid.Row centered textAlign="center">
                      <Button as="div" labelPosition="right">
                        <ContinueButton data={data} size="small">
                          <Icon className="play" /> {t`Continue`} 「
                          {data?.times_read}」
                        </ContinueButton>
                        <Label basic color="orange" pointing="left">
                          {Math.round(data?.progress?.percent)}%
                        </Label>
                      </Button>
                    </Grid.Row>
                  )}
                  <Grid.Row centered textAlign="center">
                    <Button.Group size="small">
                      {sameMachine && (
                        <Button
                          icon="external"
                          toggle
                          title={t`Open in external viewer`}
                        />
                      )}
                      <Link
                        href={urlstring(`/item/gallery/${data?.id}/page/1`)}
                        passHref
                        legacyBehavior
                      >
                        <Button as="a" primary>
                          <Icon className="book open" /> {t`Read`} 「
                          {data?.times_read}」
                        </Button>
                      </Link>
                      <Button.Or text={t`Or`} />
                      <Button
                        color="red"
                        basic={!inReadingQueue}
                        onClick={useCallback(() => {
                          if (inReadingQueue) {
                            setReadingQueue(
                              readingQueue.filter((i) => i !== data?.id)
                            );
                          } else {
                            setReadingQueue([...readingQueue, data?.id]);
                          }
                        }, [readingQueue, data?.id, inReadingQueue])}
                        title={
                          inReadingQueue
                            ? t`Remove from reading queue`
                            : t`Add to reading queue`
                        }
                      >
                        <Icon
                          name={
                            inReadingQueue ? 'bookmark' : 'bookmark outline'
                          }
                        />{' '}
                        {t`Queue`}
                      </Button>
                    </Button.Group>
                  </Grid.Row>
                  <Grid.Row>
                    <LabelFields>
                      <LabelField label={t`Rating`}>
                        <RatingLabel size="massive" />
                      </LabelField>
                      <LabelField label={t`Artist`}>
                        <ArtistLabels />
                      </LabelField>

                      <LabelField label={t`Circle`}>
                        <CircleLabels />
                      </LabelField>
                      <LabelField label={t`Language`}>
                        <LanguageLabel>{data?.language?.name}</LanguageLabel>
                      </LabelField>
                      <LabelField label={t`Category`}>
                        <CategoryLabel />
                      </LabelField>

                      <LabelField label={t`Published`}>
                        <DatePublishedLabel />
                      </LabelField>
                    </LabelFields>
                  </Grid.Row>
                  {isMobileMax && <Grid.Row>{detailsSegment}</Grid.Row>}
                </Grid>
              </div>
              {isTabletMin && detailsSegment}
            </div>
          </Segment>
        </Container>
      </DataContext.Provider>
    </>
  );
}
