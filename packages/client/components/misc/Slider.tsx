import '@brainhubeu/react-carousel/lib/style.css';
import 'swiper/css/bundle';

import classNames from 'classnames';
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Icon, Label, Segment } from 'semantic-ui-react';
import SwiperCore, { Autoplay, Navigation } from 'swiper/core';
import { Swiper, SwiperSlide } from 'swiper/react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../shared/enums';
import { ServerGallery, ServerItem } from '../../shared/types';
import { MiscState } from '../../state';
import { useInitialRecoilState } from '../../state/index';
import GalleryCard, { galleryCardDataFields } from '../item/Gallery';
import { EmptySegment, Visible } from './index';

export const SliderElement = SwiperSlide;

export function SliderNav({
  direction,
  onClick,
  disabled,
}: {
  direction: 'left' | 'right';
  disabled?: boolean;
  onClick?: Function;
}) {
  return (
    <Icon
      disabled={disabled}
      name={classNames('chevron', direction)}
      onClick={onClick}
      circular
      inverted
      link
      className={classNames(`slide-next-${direction}`, 'slide-next')}
    />
  );
}

export function Slider({
  show: initialShow,
  defaultShow,
  stateKey,
  infinite,
  children,
  topPadding,
  fluid,
  label,
  showCount = true,
  touchStartPreventDefault = false,
  color,
  autoplay,
  className,
  ...props
}: {
  show?: boolean;
  defaultShow?: boolean;
  stateKey?: string;
  fluid?: boolean;
  loading?: boolean;
  infinite?: boolean;
  topPadding?: boolean;
  showCount?: boolean;
  touchStartPreventDefault?: boolean;
  autoplay?: boolean;
  label?: React.ReactNode;
} & React.ComponentProps<typeof Segment>) {
  const [open, setOpen] = useInitialRecoilState(
    MiscState.labelAccordionOpen(stateKey),
    initialShow ?? defaultShow
  );

  const swiper = useRef<SwiperCore>();

  const items = React.Children.toArray(children);

  useEffect(() => {
    if (swiper.current) {
      swiper.current.update();
    }
  }, [children]);

  const onLabelClick = useCallback(
    (e) => {
      e.preventDefault();
      if (initialShow === undefined) {
        setOpen(!open);
      }
    },
    [open]
  );

  const onSwiper = useCallback((s) => {
    swiper.current = s;
  }, []);

  const onAutoplay = useMemo(
    () =>
      autoplay
        ? {
            delay: 10000,
            pauseOnMouseEnter: true,
            disableOnInteraction: false,
            stopOnLastSlide: false,
          }
        : undefined,
    [autoplay]
  );

  const navigation = useMemo(
    () => ({
      nextEl: '.slide-next-right',
      prevEl: '.slide-next-left',
    }),
    []
  );

  const breakpoints = useMemo(
    () => ({
      460: {
        slidesPerView: 2,
        slidesPerGroup: 2,
      },
      675: {
        slidesPerView: 3,
        slidesPerGroup: 3,
      },
      980: {
        slidesPerView: 4,
        slidesPerGroup: 3,
      },
      1200: {
        slidesPerView: 5,
        slidesPerGroup: 3,
      },
      1800: {
        slidesPerView: 6,
        slidesPerGroup: 3,
      },
    }),
    []
  );

  return (
    <Segment
      basic
      {...props}
      className={classNames('swiper', className, { fluid: fluid })}>
      {!!label && (
        <Label
          color={color}
          attached="top"
          as={initialShow === false ? undefined : 'a'}
          onClick={onLabelClick}>
          <Icon name={open ? 'caret down' : 'caret right'} />
          {label}
          {showCount && <Label.Detail>{items.length}</Label.Detail>}
        </Label>
      )}
      <Visible visible={initialShow || open}>
        {!items.length && <EmptySegment />}
        {items && (
          <Swiper
            onSwiper={onSwiper}
            modules={[Autoplay, Navigation]}
            autoplay={onAutoplay}
            loop={infinite}
            slidesPerView={3}
            watchOverflow
            touchStartPreventDefault={touchStartPreventDefault}
            navigation={navigation}
            breakpoints={breakpoints}>
            {children}
            <SliderNav direction="left" />
            <SliderNav direction="right" />
          </Swiper>
        )}
      </Visible>
    </Segment>
  );
}

export function SimilarItemsSlider({
  type,
  stateKey,
  item,
  ...props
}: {
  type: ItemType;
  stateKey?: string;
  item: DeepPick<ServerItem, 'id'>;
} & React.ComponentProps<typeof Slider>) {
  const [data, setData] = useState<ServerGallery[]>([]);

  const { data: cmd, isLoading } = useQueryType(
    QueryType.SIMILAR,
    {
      item_id: item?.id,
      item_type: type,
      fields: galleryCardDataFields,
      limit: 50,
    },
    {
      enabled: !!item?.id,
    }
  );

  const [loading, setLoading] = useState(isLoading);

  useCommand(
    cmd?.data,
    {},
    (v) => {
      const d = setData(v?.items as ServerGallery[]);
      setLoading(false);
    },
    []
  );

  useEffect(() => {
    if (isLoading) {
      setLoading(true);
    }
  }, [isLoading]);

  return (
    <Slider
      autoplay
      loading={loading}
      stateKey={stateKey}
      showCount={false}
      label={t`Just like this one`}
      {...props}>
      {data.map((i) => (
        <SliderElement key={i.id}>
          <GalleryCard size="small" data={i} />
        </SliderElement>
      ))}
    </Slider>
  );
}
