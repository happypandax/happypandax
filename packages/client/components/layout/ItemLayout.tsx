import classNames from 'classnames';
import ColorThief from 'colorthief';
import Link from 'next/link';
import React, {
  RefObject,
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from 'react';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import {
  Button,
  Container,
  Divider,
  Grid,
  Header,
  Icon,
  Image,
  Label,
  Menu,
  Segment,
} from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useRefEvent } from '../../hooks/utils';
import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ServerGallery } from '../../misc/types';
import { animateCSS, urlstring } from '../../misc/utility';
import { AppState, DataState } from '../../state';
import {
  ArtistLabels,
  CircleLabels,
  DateAddedLabel,
  DatePublishedLabel,
  GroupingLabel,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  NameTable,
  ParodyLabels,
  TagsTable,
  UrlList,
} from '../data/Common';
import MainMenu, { ConnectionItem, MenuItem } from '../Menu';
import styles from './ItemLayout.module.css';

function ParallaxDiv({
  children,
  target,

  className,
  ...props
}: { target?: RefObject<HTMLElement | Document> } & Omit<
  React.HTMLProps<HTMLDivElement>,
  'target'
>) {
  const targetRef = target ?? useRef(window?.document);
  const ref = useRef<HTMLDivElement>();
  const runningAnimationRef = useRef({
    running: false,
    startPos: 0,
    lastOffset: 0,
    velocity: 0.5,
    ease: 0.05,
  });

  useRefEvent(
    targetRef,
    'scroll',
    (ev) => {
      if (!ref.current) {
        return;
      }

      if (!runningAnimationRef.current.running) {
        runningAnimationRef.current.running = true;

        if (runningAnimationRef.current.startPos) {
          runningAnimationRef.current.startPos = ref.current.offsetTop;
        }

        const loop = () => {
          if (!ref.current) {
            return;
          }

          const offset = window.scrollY;
          const delta =
            (offset - runningAnimationRef.current.lastOffset) *
            runningAnimationRef.current.velocity *
            runningAnimationRef.current.ease;

          if (Math.abs(delta) < 0.05) {
            runningAnimationRef.current.lastOffset = offset;
            runningAnimationRef.current.running = false;
            return;
          }

          ref.current.style.transform = `translate(0, ${
            runningAnimationRef.current.startPos -
            runningAnimationRef.current.lastOffset
          }px)`;

          runningAnimationRef.current.lastOffset += delta;
          requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
      }
    },
    { passive: true },
    []
  );

  return (
    <div ref={ref} {...props} className={classNames(className)}>
      {children}
    </div>
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
  | 'metatags.favorite'
  | 'metatags.read'
  | 'metatags.readlater'
  | 'metatags.inbox'
  | 'progress.end'
  | 'progress.page.number'
  | 'progress.percent'
  | 'language.code'
  | 'language.name'
  | 'last_read'
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
  'circles.name',
  'profile',
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

function LabelFields({
  children,
  className,
  ...props
}: React.HTMLProps<HTMLDivElement>) {
  return (
    <div {...props} className={classNames('ui form', className)}>
      {children}
    </div>
  );
}

function LabelField({
  label,
  children,
  padded = true,
}: {
  padded?: boolean;
  label?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <div
        className={classNames(styles.label_children, {
          [styles.label_children_padded]: padded,
        })}>
        {children}
      </div>
    </div>
  );
}

export function GalleryItemHeader({ data }: { data: GalleryHeaderData }) {
  const contextKey = 'header_' + DataState.getKey(ItemType.Gallery, data);
  const heroRef = useRef<HTMLDivElement>();
  const heroImgRef = useRef<HTMLImageElement>();
  const colorThief = useMemo(() => new ColorThief(), []);

  const [readingQueue, setReadingQueue] = useRecoilState(AppState.readingQueue);

  const sameMachine = useRecoilValue(AppState.sameMachine);
  const setData = useSetRecoilState(DataState.data(contextKey));

  useEffect(() => {
    setData(data as PartialExcept<ServerGallery, 'id'>);
    animateCSS(heroImgRef.current, styles.fadeInDownImage, false);
  }, [data]);

  useEffect(() => {
    const setColor = () => {
      const c = colorThief.getColor(heroImgRef.current);
      heroRef.current.style.backgroundColor = `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
    };
    if (heroImgRef.current.complete) {
      setColor();
    } else {
      heroImgRef.current.onload = setColor;
    }
  }, [data]);

  const hasProgress = !!data?.progress && !data?.progress?.end;

  const inReadingQueue = readingQueue?.includes?.(data?.id);

  return (
    <DataContext.Provider value={{ key: contextKey, type: ItemType.Gallery }}>
      <div ref={heroRef} className={classNames(styles.header_hero)}>
        <Container className="pos-relative">
          <ParallaxDiv>
            <img
              className="animate__slower"
              ref={heroImgRef}
              src={data.profile.data}
            />
          </ParallaxDiv>
        </Container>
      </div>
      <Container>
        <Segment basic className="no-margins no-top-padding no-right-padding">
          <div className={classNames(styles.header_content)}>
            <div className={styles.cover_column}>
              <Image
                centered
                rounded
                id={styles.cover}
                src={data.profile.data}
                width={data.profile.size[0]}
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
              <Divider hidden />
              <Grid>
                {hasProgress && (
                  <Grid.Row centered textAlign="center">
                    <Button as="div" labelPosition="right">
                      <Button color="orange" size="small">
                        <Icon className="play" /> {t`Continue`}
                      </Button>
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
                      passHref>
                      <Button as="a" primary>
                        <Icon className="book open" /> {t`Read`}
                      </Button>
                    </Link>
                    <Button.Or text={t`Or`} />
                    {!data?.metatags?.readlater && (
                      <Button>
                        <Icon name="bookmark outline" /> {t`Save for later`}
                      </Button>
                    )}
                    {data?.metatags?.readlater && (
                      <Button positive>
                        <Icon name="bookmark" /> {t`Saved for later`}
                      </Button>
                    )}
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
                      icon="open book"
                      title={
                        inReadingQueue
                          ? t`Remove from reading queue`
                          : t`Add to reading queue`
                      }
                    />
                  </Button.Group>
                </Grid.Row>
                <Grid.Row>
                  <LabelFields>
                    <LabelField label={t`Rating`}>test</LabelField>
                    <LabelField label={t`Artist`}>
                      <ArtistLabels />
                    </LabelField>

                    <LabelField label={t`Circle`}>
                      <CircleLabels />
                    </LabelField>
                    <LabelField label={t`Parody`}>
                      <ParodyLabels />
                    </LabelField>
                    <LabelField label={t`Language`}>
                      <LanguageLabel>{data?.language?.name}</LanguageLabel>
                    </LabelField>

                    <LabelField label={t`Published`}>
                      <DatePublishedLabel />
                    </LabelField>
                  </LabelFields>
                </Grid.Row>
              </Grid>
            </div>
            <Segment className="no-margins no-right-padding" basic>
              <NameTable
                dataKey="titles"
                dataPrimaryKey="preferred_title"></NameTable>
              <Header textAlign="center">
                <LastReadLabel timestamp={data?.last_read} />
                <LastUpdatedLabel timestamp={data?.last_updated} />
                <DateAddedLabel timestamp={data?.timestamp} />
              </Header>
              <Divider hidden className="small" />
              <LabelFields>
                <LabelField label={t`Series`} padded={false}>
                  <GroupingLabel />
                </LabelField>
                <LabelField label={t`Tags`} padded={false}>
                  <TagsTable />
                </LabelField>
                <LabelField label={t`External links`} padded={false}>
                  <UrlList />
                </LabelField>
              </LabelFields>
            </Segment>
          </div>
        </Segment>
      </Container>
    </DataContext.Provider>
  );
}

export function ItemMenu({
  data,
  children,
}: {
  data: DeepPick<
    ServerGallery,
    | 'id'
    | 'metatags.favorite'
    | 'metatags.read'
    | 'metatags.inbox'
    | 'metatags.readlater'
  >;
  children?: React.ReactNode;
}) {
  const readingQueue = useRecoilValue(AppState.readingQueue);

  return (
    <MainMenu absolutePosition size="mini" connectionItem={false}>
      <MenuItem icon="heart" color="red"></MenuItem>
      {children}
      <Menu.Menu position="right">
        {readingQueue?.includes?.(data?.id) && (
          <MenuItem
            icon={{
              className: 'book open',
              color: 'red',
              bordered: true,
              inverted: true,
            }}
            title={`This item is in your reading queue`}></MenuItem>
        )}
        {data?.metatags?.inbox && (
          <MenuItem
            icon={{ name: 'inbox', bordered: true, inverted: true }}
            title={`This item is in your inbox`}></MenuItem>
        )}
        {data?.metatags?.readlater && (
          <MenuItem
            icon={{ name: 'bookmark', bordered: true, inverted: true }}
            title={`Saved for later`}></MenuItem>
        )}
        {!data?.metatags?.read && (
          <MenuItem
            icon={{ name: 'eye slash outline', bordered: true, inverted: true }}
            title={`This item has not been read yet`}></MenuItem>
        )}
        <ConnectionItem />
      </Menu.Menu>
    </MainMenu>
  );
}
