import classNames from 'classnames';
import Link from 'next/link';
import { useRouter } from 'next/router';
import React, { useCallback, useContext, useEffect, useState } from 'react';
import { useHarmonicIntervalFn } from 'react-use';
import { useRecoilState, useRecoilValue } from 'recoil';
import {
  Button,
  Checkbox,
  Form,
  Grid,
  Header,
  Icon,
  Label,
  Modal,
  Segment,
  Transition,
} from 'semantic-ui-react';

import { DataContext, ReaderContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { ImageSize, ItemType } from '../../shared/enums';
import { ServerCategory, ServerGallery } from '../../shared/types';
import { urlparse, urlstring } from '../../shared/utility';
import { AppState, ReaderState } from '../../state';
import { FavoriteLabel, RatingLabel } from '../dataview/Common';
import CollectionCard, { CollectionCardData } from '../item/Collection';
import GalleryCard, {
  GalleryCardData,
  galleryCardDataFields,
} from '../item/Gallery';
import { SimilarItemsSlider, Slider, SliderElement } from '../misc/Slider';

function ReadNext({
  random,
  nextChapter,
  randomItems,
  nextInReadingList,
}: {
  random?: DeepPick<ServerGallery, 'id'>;
  randomItems?: GalleryCardData[];
  nextChapter?: GalleryCardData;
  nextInReadingList?: GalleryCardData;
}) {
  const { stateKey } = useContext(ReaderContext);

  const router = useRouter();
  const isEnd = useRecoilValue(ReaderState.endReached(stateKey));
  const readNextCountdown = useRecoilValue(
    ReaderState.autoReadNextCountdown(stateKey)
  );

  const [countDownEnabled, setCountDownEnabled] = useState<
    'queue' | 'chapter' | 'readinglist'
  >();

  const [countdown, setCountdown] = useState(readNextCountdown);
  const readingQueue = useRecoilValue(AppState.readingQueue);

  const { data: queueData, isLoading } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: readingQueue?.[0],
      profile_options: { size: ImageSize.Medium },
      fields: galleryCardDataFields,
    },
    { enabled: !!readingQueue.length }
  );

  useHarmonicIntervalFn(
    () => {
      if (countdown === 1) {
        let nextId = 0;
        switch (countDownEnabled) {
          case 'chapter':
            nextId = nextChapter.id;
            break;
          case 'queue':
            nextId = queueData.data.id;
            break;
          case 'readinglist':
            nextId = nextInReadingList.id;
            break;
        }

        if (nextId) {
          router.push(
            urlstring(`/item/gallery/${nextId}/page/1`, urlparse().query as any)
          );
        }
      }
      setCountdown(Math.max(countdown - 1, 0));
    },
    isEnd && !isLoading && countDownEnabled && countdown ? 1000 : null
  );

  useEffect(() => {
    const t = readNextCountdown;
    if (queueData) {
      setCountDownEnabled('queue');
      setCountdown(t);
    } else if (nextChapter) {
      setCountDownEnabled('chapter');
      setCountdown(t);
    } else if (nextInReadingList) {
      setCountDownEnabled('readinglist');
      setCountdown(t);
    } else {
      setCountDownEnabled(undefined);
    }
  }, [isEnd, nextChapter, nextInReadingList, queueData, readNextCountdown]);

  const onlyRandom =
    randomItems?.length && !queueData && !nextChapter && !nextInReadingList;

  return (
    <Grid
      centered
      columns="equal"
      onClick={() => {
        setCountDownEnabled(undefined);
      }}>
      <Grid.Row>
        <Grid.Column textAlign="center">
          <Header
            textAlign="center"
            size="medium">{t`Read the next one`}</Header>
          {!!random && (
            <Link
              passHref
              href={urlstring(
                `/item/gallery/${random.id}/page/1`,
                urlparse().query as any
              )}
              legacyBehavior>
              <Button as="a">{t`Pick a random`}</Button>
            </Link>
          )}
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        {!!queueData && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next in queue...`}{' '}
                {countDownEnabled === 'queue'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard
                size="medium"
                data={queueData.data as ServerGallery}
              />
            </Segment>
          </Grid.Column>
        )}

        {!!nextChapter && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next chapter...`}{' '}
                {countDownEnabled === 'chapter'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard size="medium" data={nextChapter} />
            </Segment>
          </Grid.Column>
        )}

        {!!nextInReadingList && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next in reading list...`}{' '}
                {countDownEnabled === 'readinglist'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard size="medium" data={nextInReadingList} />
            </Segment>
          </Grid.Column>
        )}

        {onlyRandom &&
          randomItems.map((g) => (
            <Grid.Column key={g.id} textAlign="center">
              <Segment tertiary basic>
                <GalleryCard size="medium" data={g} />
              </Segment>
            </Grid.Column>
          ))}
      </Grid.Row>
    </Grid>
  );
}

function RatingIcon({
  animation = 'shake',
  ...props
}: React.ComponentProps<typeof Icon> & {
  animation?: React.ComponentProps<typeof Transition>['animation'];
}) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    if (animated) {
      setTimeout(() => setAnimated(false), 500);
    }
  }, [animated]);

  return (
    <Icon
      {...props}
      className={classNames(props.className, 'transition', {
        [animation]: animated,
      })}
      onClick={useCallback(
        (...args) => {
          props?.onClick?.(...args);
          setAnimated(true);
        },
        [props?.onClick]
      )}
    />
  );
}

function EndRating() {
  const { item } = useContext(ReaderContext);

  // TODO: rating doesnt update to server
  const [rating, setRating] = useState(item?.rating);

  return (
    <Grid as={Segment} basic textAlign="center">
      <Grid.Row>
        <Grid.Column>
          <RatingIcon
            className="meh outline"
            animation="shake"
            link
            onClick={useCallback(() => setRating(rating < 2 ? 2 : 3), [rating])}
            size="big"
          />
        </Grid.Column>
        <Grid.Column>
          <RatingIcon
            className="meh rolling eyes outline"
            link
            animation="pulse"
            onClick={useCallback(
              () => setRating(rating < 4 ? 4 : rating < 5 ? 5 : 6),
              [rating]
            )}
            size="big"
            color="yellow"
          />
        </Grid.Column>
        <Grid.Column>
          <RatingIcon
            link
            animation="jiggle"
            onClick={useCallback(() => setRating(rating < 7 ? 7 : 8), [rating])}
            className="flushed outline"
            size="big"
            color="orange"
          />
        </Grid.Column>
        <Grid.Column>
          <RatingIcon
            link
            animation="tada"
            onClick={useCallback(() => setRating(rating < 9 ? 9 : 10), [
              rating,
            ])}
            className="grin hearts outline"
            size="big"
            color="red"
          />
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <RatingLabel
          size="massive"
          onRating={useCallback((r) => setRating(r), [])}
          defaultRating={rating}
        />
      </Grid.Row>
      <span className="left-0 pos-absolute">
        <FavoriteLabel
          size="massive"
          defaultRating={item?.metatags?.favorite ? 1 : 0}
        />
      </span>
      <div className="right-0 pos-absolute">
        <Link href={`/item/gallery/${item.id}`} passHref legacyBehavior>
          <Button as="a" icon={{ name: 'level up alternate' }} basic />
        </Link>
        {item?.metatags?.inbox && <Button primary>{t`Send to library`}</Button>}
      </div>
    </Grid>
  );
}

function CollectionOptions(props: React.ComponentProps<typeof Modal>) {
  const { data } = useQueryType(QueryType.ITEMS, {
    item_type: ItemType.Category,
    fields: ['name'],
  });

  const [cats, setCats] = useRecoilState(ReaderState.collectionCategories);

  return (
    <Modal closeIcon size="small" {...props}>
      <Modal.Header>{t`Categories`}</Modal.Header>
      <Modal.Content>
        <Form>
          {data &&
            data?.data?.items?.map((i: ServerCategory) => (
              <Form.Field
                key={i.id}
                defaultChecked={cats.includes(i.name)}
                onChange={(e, d) => {
                  e.preventDefault();
                  if (d.checked) {
                    setCats([...cats, i.name]);
                  } else {
                    setCats(cats.filter((x) => x !== i.name));
                  }
                }}
                control={Checkbox}
                label={i.name}
              />
            ))}
        </Form>
      </Modal.Content>
    </Modal>
  );
}

export default function EndContent({
  sameArtist = [],
  series = [],
  collections = [],
  ...readNextProps
}: {
  sameArtist?: GalleryCardData[];
  series?: GalleryCardData[];
  collections?: CollectionCardData[];
} & React.ComponentProps<typeof ReadNext>) {
  const { item, stateKey } = useContext(ReaderContext);

  const { dataContext } = useSetupDataState({
    initialData: item,
    itemType: ItemType.Gallery,
    key: stateKey,
  });

  const collectionCategories = useRecoilValue(ReaderState.collectionCategories);
  const endReached = useRecoilValue(ReaderState.endReached(stateKey));
  const [_readingQueue, setReadingQueue] = useRecoilState(
    AppState.readingQueue
  );
  const readingQueue = _readingQueue.filter((n) => n !== item?.id);

  useEffect(() => {
    if (endReached) {
      if (_readingQueue.includes(item.id)) {
        setReadingQueue(readingQueue);
      }
    }
  }, [endReached, item]);

  const { data: queueData } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: readingQueue,
      profile_options: { size: ImageSize.Small },
      fields: galleryCardDataFields,
    },
    { enabled: !!readingQueue.length }
  );

  return (
    <Grid as={Segment} centered fluid className="max-h-full overflow-auto">
      <Grid.Row>
        <Grid.Column width={16}>
          <Header
            textAlign="center"
            size="large">{t`What did you think?`}</Header>
        </Grid.Column>
        <Grid.Column width={16} textAlign="center">
          <DataContext.Provider value={dataContext}>
            <EndRating />
          </DataContext.Provider>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <ReadNext {...readNextProps} />
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="this_queue"
            defaultOpen={false}
            label={t`Queue`}
            color="red">
            {((queueData?.data as any) as ServerGallery[])?.map?.((g) => (
              <SliderElement key={g.id}>
                <GalleryCard size="small" data={g} />
              </SliderElement>
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      {!!series.length && (
        <Grid.Row>
          <Grid.Column>
            <Slider stateKey="series" label={t`Series`} color="teal">
              {series.map((i) => (
                <SliderElement key={i.id}>
                  <GalleryCard size="small" data={i} />
                </SliderElement>
              ))}
            </Slider>
          </Grid.Column>
        </Grid.Row>
      )}
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="collections"
            autoplay
            padded
            showCount={false}
            label={
              <>
                {t`Collections`}
                <Label.Detail>{collectionCategories.join(', ')}</Label.Detail>
                <CollectionOptions
                  trigger={
                    <Button
                      floated="right"
                      icon="setting"
                      size="mini"
                      compact
                      inverted
                      basic
                    />
                  }
                />
              </>
            }
            defaultShow={false}
            color="violet">
            {collections.map((i) => (
              <SliderElement key={i.id}>
                <CollectionCard size="small" data={i} />
              </SliderElement>
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="same_artist"
            label={t`From same artist`}
            defaultShow={!sameArtist?.length}
            color="blue">
            {sameArtist.map((i) => (
              <SliderElement key={i.id}>
                <GalleryCard size="small" data={i} />
              </SliderElement>
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <SimilarItemsSlider item={item} type={ItemType.Gallery} />
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}
