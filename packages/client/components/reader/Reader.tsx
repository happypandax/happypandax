import classNames from 'classnames';
import _ from 'lodash';
import { action, autorun, makeAutoObservable, toJS } from 'mobx';
import { observer } from 'mobx-react-lite';
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useUnmount, useUpdateEffect } from 'react-use';
import { useSetRecoilState } from 'recoil';
import { Dimmer, Label, Segment } from 'semantic-ui-react';

import { ReaderContext } from '../../client/context';
import { useHijackHistory } from '../../client/hooks/ui';
import {
  useEffectAction,
  useUpdateEffectAction,
} from '../../client/hooks/utils';
import {
  MutatationType,
  Query,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { getClientWidth, update } from '../../client/utility';
import {
  ImageSize,
  ItemFit,
  ItemType,
  ReadingDirection,
} from '../../shared/enums';
import {
  FieldPath,
  ReaderData,
  ServerItem,
  ServerPage,
} from '../../shared/types';
import { asyncDebounce } from '../../shared/utility';
import {
  ReaderState,
  useInitialRecoilState,
  useInitialRecoilValue,
} from '../../state';
import Canvas, { CanvasState } from './Canvas';
import CanvasImage from './CanvasImage';

/**
 * Utility function to generate a window of pages around the current page
 *
 * @param page current page
 * @param size window size
 * @param total total number of pages
 * @param startIndex index of first page
 * @returns
 */
function windowedPages(
  page: number,
  size: number,
  total: number,
  startIndex: number = 0
) {
  if (!total) return [];

  const start = startIndex - 1;

  page = Math.min(page, total);
  page = Math.max(page, start);

  const pages = [];
  if (page > start) {
    let i = 1;
    while (page - i > start && i < size / 2) {
      pages.unshift(page - i);
      i++;
    }
  }

  pages.push(page);

  if (page < total) {
    let i = 1;
    while (page + i <= total && i < size / 2 + 1) {
      pages.push(page + i);
      i++;
    }
  }
  return pages;
}

function getOptimalImageSize() {
  const w = getClientWidth();
  if (w > 2400) return ImageSize.Original;
  if (w > 1600) return ImageSize.x2400;
  else if (w > 1280) return ImageSize.x1600;
  else if (w > 980) return ImageSize.x1280;
  else if (w > 768) return ImageSize.x960;
  else return ImageSize.x768;
}

const pageFields: FieldPath<ServerPage>[] = [
  'id',
  'name',
  'number',
  'metatags.favorite',
  'metatags.inbox',
  'metatags.trash',
  'path',
];

const PLACEHOLDERS = _.range(59).map((p) => ({
  number: p + 1,
  url: `https://via.placeholder.com/1400x2200/cc${(10 * (p + 1)).toString(
    16
  )}cc/ffffff?text=Page+${p + 1}`,
}));

class InternalReaderState {
  scaling: 0 | ImageSize = 0;
  lastReadPageId: number = 0;

  pageFocus: number = 0;
  // indexes of pages that are currently active
  pageWindow: number[] = [];
  pages: ReaderData[] = [];

  // Two layers of "windows", one for the actual pages fetched from the server (remote), another for the active pages to be loaded (images) for the client (local)
  // When the local window runs out of pages, the remote window readjusts and fetches more pages if needed

  windowSize: number = 25;
  remoteWindowSize: number = 40;

  // how close to the edge of the window to update the local window
  windowEdgeOffset: number = 1;
  // same as above but for the remote window
  remoteWindowEdgeOffset: number = 4;

  fetchingMore = {
    fetching: false,

    previousNumber: 0,
  };
  fetchingImages: number[] = [];
  retryImages: { [k: number]: number } = {};

  private _lastScaling: 0 | ImageSize = 0;
  private _initialPageNumber: number;

  // keep track of image refetch retries
  maxRetries = 3;

  private _disposers: Array<() => void>;

  constructor(initialPageNumber: number = 1) {
    this._initialPageNumber = initialPageNumber;

    this._disposers = [];

    makeAutoObservable(this);
  }

  get currentPage() {
    return this.pages?.[this.pageWindow?.[this.pageFocus]];
  }

  setScaling(scaling: 0 | ImageSize) {
    this.scaling = scaling;

    // fetch images with new scaling
    if (!this.fetchingImages) {
      this.fetchingImages = [];
    }

    this.fetchCurrentWindowImages();
  }

  setPages(pages: ReaderData[]) {
    this.pages = pages;
    this.debouncedUpdateLocalWindow();
  }

  setPageWindow(window: number[]) {
    this.pageWindow = window;

    // fetch missing images from the server if needed
    if (this.pageWindow.length) {
      this.fetchCurrentWindowImages();
    }
  }

  setWindowSize(size: number, pageCount?: number) {
    this.windowSize = Math.min(size, this.pages.length || (pageCount ?? 1));
    this.debouncedUpdateLocalWindow();
  }

  setRemoteWindowSize(size: number, pageCount?: number) {
    this.remoteWindowSize = Math.max(
      40,
      size ?? Math.ceil(this.windowSize * 2)
    );
    this.debouncedUpdateLocalWindow();
  }

  setPageFocus(focus: number, pageNumber?: number) {
    this.pageFocus = focus;

    let needsUpdate = false;
    if (this.pageFocus <= this.windowEdgeOffset) {
      needsUpdate = true;
    } else if (
      Math.abs(this.pageWindow.length - this.pageFocus) <= this.windowEdgeOffset
    ) {
      needsUpdate = true;
    }

    if (needsUpdate) {
      this.updateLocalWindow(pageNumber);
    }
  }

  /**
   * Local window, sets window of active local pages based on page number
   * @param pageNumber force window around this page number
   * @returns
   */
  updateLocalWindow(pageNumber?: number) {
    if (this.fetchingMore.fetching) {
      return;
    }

    const currentPageNumber =
      pageNumber ?? this.currentPage?.number ?? this._initialPageNumber;

    const idx = Math.max(
      0,
      this.pages.findIndex((p) => p.number === currentPageNumber)
    );

    const windowed = windowedPages(
      idx,
      this.windowSize,
      Math.max(this.pages.length - 1, 0)
    );

    // correct focus, this is after more pages have been fetched, then the focus may point at the wrong page
    windowed.forEach((n, i) => {
      if (this.pages[n].number === currentPageNumber && i !== this.pageFocus) {
        this.pageFocus = i;
      }
    });

    if (!_.isEqual(this.pageWindow, windowed)) {
      this.setPageWindow(windowed);
    }
  }

  debouncedUpdateLocalWindow = _.debounce(this.updateLocalWindow, 100);

  resetProfiles() {
    this.pages = update(this.pages, {
      $set: (i) => ({ ...i, profile: undefined }),
    });
    this.retryImages = {};
    this.fetchingImages = [];
    this.fetchingMore.previousNumber = 0;
    this.fetchingMore.fetching = false;
  }

  fetchMoreRemotePages = asyncDebounce(async function fetchMoreRemotePages(
    this: InternalReaderState,
    item: Pick<ServerItem, 'id'>,
    pageCount: number,
    pageNumber: number
  ) {
    if (isNaN(this.pageFocus)) {
      return false;
    }

    const pNumber = this.pageWindow.length
      ? this.currentPage.number
      : pageNumber;

    let fetchMore: 'left' | 'right' = undefined;

    if (this.pageWindow.length) {
      // how close to the edge of the local window needed to be before more pages should be fetched
      const offset = Math.min(Math.floor(this.windowSize / 2), 2);

      const leftPageFocusOffset = Math.max(this.pageFocus - (offset - 1), 0);
      const rightPageFocusOffset = Math.min(
        this.pageFocus + (offset + 1),
        this.pageWindow.length - 1
      );

      // when close to the left side of the remote window and the page on the left side is not the first, fetch more
      if (
        this.pageWindow[leftPageFocusOffset] <= this.remoteWindowEdgeOffset &&
        this.pages[0].number !== 1
      ) {
        fetchMore = 'left';
      }
      // when close to the right side of the remote window and the page on the right side is not the last, fetch more
      else if (
        Math.abs(this.pages.length - this.pageWindow[rightPageFocusOffset]) <=
          this.remoteWindowEdgeOffset &&
        this.pages[this.pages.length - 1].number !== pageCount
      ) {
        fetchMore = 'right';
      }
    } else if (this.pages.length || pageCount) {
      fetchMore = 'left';
    }

    console.debug('fetching more pages:', fetchMore);
    //   {
    //     pageFocus: this.pageFocus,
    //     pageWindow: [...this.pageWindow],
    //     fetching: this.fetchingMore.fetching,
    //     previousNumber: this.fetchingMore.previousNumber,
    //     currentPage: pNumber,
    //     pages: this.pages.length,

    //   })

    if (
      fetchMore &&
      !this.fetchingMore.fetching &&
      (!this.pages.length || this.fetchingMore.previousNumber !== pNumber)
    ) {
      // when the focus gets corrected by the local window, this hook will retrigger so we need to make sure we don't refetch
      this.fetchingMore.previousNumber = pNumber;

      this.fetchingMore.fetching = true;
      return await Query.fetch(QueryType.PAGES, {
        gallery_id: item.id,
        number: pNumber,
        fields: pageFields,
        window_size: this.remoteWindowSize,
      })
        .then((r) => {
          // required, or pageWindow hook won't see it in time
          this.fetchingMore.fetching = false;
          this.setPages(r.data.items as ReaderData[]);
          return r.data.count;
        })
        .finally(() => {
          // in case of error
          this.fetchingMore.fetching = false;
        });
    }

    return false;
  },
  100);

  fetchCurrentWindowImages() {
    // only if not already fetching
    if (
      this.pageWindow.length &&
      !this.fetchingImages.includes(
        this.pages[this.pageWindow[this.pageWindow.length - 1]].id
      )
    ) {
      // only pages that dont have profile data and not currently fetching
      const fetch_ids: number[] = [];
      this.pageWindow
        .map((i) => this.pages[i])
        .filter((p) => {
          if (this._lastScaling !== this.scaling) {
            return true;
          }

          return !p?.profile?.data;
        })
        .forEach((p) => {
          if (this.retryImages[p.id] === undefined) {
            this.retryImages[p.id] = -1;
          }

          // if max retries reached, do nothing
          if (this.retryImages[p.id] >= this.maxRetries) {
            return;
          }

          if (!this.fetchingImages.includes(p.id)) {
            this.retryImages[p.id]++;
            this.fetchingImages.push(p.id);
            fetch_ids.push(p.id);
          }
        });

      if (fetch_ids.length) {
        // this updates page with new fetched profile

        let size = ImageSize.x1280;
        if (this.scaling !== undefined) {
          size = this.scaling === 0 ? getOptimalImageSize() : this.scaling;
        }

        this._lastScaling = size;

        Query.fetch(
          QueryType.PROFILE,
          {
            item_type: ItemType.Page,
            item_ids: fetch_ids,
            profile_options: {
              size,
            },
          },
          {
            cacheTime: 10000,
          }
        ).then((r) => {
          const spec = {};

          Object.entries(r.data).forEach(([k, v]) => {
            const pid = parseInt(k);
            const pidx = this.pages.findIndex((x) => x.id === pid);

            const r_idx = this.fetchingImages.indexOf(pid);
            if (r_idx !== -1) {
              this.fetchingImages.splice(r_idx, 1);
            }

            if (pidx !== -1) {
              spec[pidx] = {
                $set: {
                  ...this.pages[pidx],
                  profile: v,
                },
              };
            }
          });

          if (Object.keys(spec).length) {
            this.pages = update(this.pages, spec);
          }
        });
      }
    }
  }

  removePageImage(pageId: number) {
    // if max retries reached, do nothing
    if (
      this.retryImages[pageId] &&
      this.retryImages[pageId] >= this.maxRetries
    ) {
      return;
    }

    const pageIndex = this.pages.findIndex((p) => p.id === pageId);
    this.pages = update(this.pages, {
      [pageIndex]: { profile: { $set: undefined } },
    });
  }

  dispose() {
    this._disposers.forEach((d) => d());
  }
}

const Reader = observer(function Reader({
  initialData,
  pageCount: initialPageCount = 0,
  windowSize: initialWindowSize = 25,
  remoteWindowSize: initialRemoteWindowSize,
  startPage = 1,
  onPage,
  autoScroll: initalAutoScroll,
  autoScrollSpeed: initalAutoScrollSpeed,
  autoNavigate: initialAutoNavigate,
  autoNavigateInterval: initialAutoNavigateInterval,
  stretchFit: initialStretchfit,
  fit: initialFit,
  wheelZoom: initialWheelZoom,
  direction: initialDirection,
  blurryBg: initialBlurryBg,
  scaling: initialScaling,
  padded,
  children,
}: {
  initialData: ReaderData[];
  pageCount?: number;
  autoNavigateInterval?: number;
  autoScrollSpeed?: number;
  fit?: ItemFit;
  stretchFit?: boolean;
  blurryBg?: boolean;
  autoNavigate?: boolean;
  autoScroll?: boolean;
  direction?: ReadingDirection;
  scaling?: ImageSize | 0;
  windowSize?: number;
  remoteWindowSize?: number;
  onPage?: (page: ReaderData) => void;
  startPage?: number;
  wheelZoom?: boolean;
  padded?: boolean;
  children?: React.ReactNode;
}) {
  const { mutate: pageReadEvent } = useMutationType(
    MutatationType.PAGE_READ_EVENT
  );

  const { item, stateKey } = useContext(ReaderContext);

  const scaling = useInitialRecoilValue(
    ReaderState.scaling(stateKey),
    initialScaling
  );
  const wheelZoom = useInitialRecoilValue(
    ReaderState.wheelZoom(stateKey),
    initialWheelZoom
  );
  const blurryBg = useInitialRecoilValue(
    ReaderState.blurryBg(stateKey),
    initialBlurryBg
  );
  const stretchFit = useInitialRecoilValue(
    ReaderState.stretchFit(stateKey),
    initialStretchfit
  );
  const autoScroll = useInitialRecoilValue(
    ReaderState.autoScroll(stateKey),
    initalAutoScroll
  );
  const autoScrollSpeed = useInitialRecoilValue(
    ReaderState.autoScrollSpeed(stateKey),
    initalAutoScrollSpeed
  );
  const autoNavigate = useInitialRecoilValue(
    ReaderState.autoNavigate(stateKey),
    initialAutoNavigate
  );
  const autoNavigateInterval = useInitialRecoilValue(
    ReaderState.autoNavigateInterval(stateKey),
    initialAutoNavigateInterval
  );
  const setAutoNavigateCounter = useSetRecoilState(
    ReaderState.autoNavigateCounter(stateKey)
  );

  const direction = useInitialRecoilValue(
    ReaderState.direction(stateKey),
    initialDirection
  );

  const fit = useInitialRecoilValue(ReaderState.fit(stateKey), initialFit);

  const [isEnd, setIsEnd] = useInitialRecoilState(
    ReaderState.endReached(stateKey),
    false
  );

  const [pageCount, setPageCount] = useInitialRecoilState(
    ReaderState.pageCount(stateKey),
    initialPageCount
  );

  const [pageNumber, setPageNumber] = useInitialRecoilState(
    ReaderState.pageNumber(stateKey),
    startPage
  );

  const setPage = useSetRecoilState(ReaderState.page(stateKey));

  const internalState = useMemo(() => {
    return new InternalReaderState(pageNumber);
  }, []);

  useUnmount(() => {
    internalState.dispose();
  });

  const canvasState = useMemo(() => {
    return new CanvasState(internalState.pageFocus);
  }, []);

  useUnmount(() => canvasState.dispose());

  useEffectAction(() => {
    internalState.setScaling(scaling);
  }, [scaling, internalState]);

  useEffectAction(() => {
    internalState.setPages(initialData);
  }, [initialData, internalState]);

  useEffectAction(() => {
    internalState.setWindowSize(initialWindowSize, pageCount);
  }, [initialWindowSize, pageCount, internalState]);

  useEffectAction(() => {
    internalState.setRemoteWindowSize(initialRemoteWindowSize, pageCount);
  }, [initialRemoteWindowSize, internalState]);

  useEffectAction(() => {
    setPageCount(initialPageCount);
  }, [initialPageCount]);

  const [countLabelVisible, setCountLabelVisible] = useState(false);

  const debouncedPageReadEvent = useCallback(
    _.debounce(
      action((lastpage: ReaderData) => {
        if (internalState.lastReadPageId !== lastpage.id) {
          pageReadEvent({ item_id: lastpage.id });
          internalState.lastReadPageId = lastpage.id;
        }
      }),
      1000
    ),
    [pageReadEvent]
  );

  // page change

  useEffect(
    () =>
      autorun(() => {
        const page = internalState.currentPage;
        if (page) {
          setPageNumber(page.number);
          debouncedPageReadEvent(page);
        }
      }),
    []
  );

  //

  useQueryType(
    QueryType.PAGES,
    {
      gallery_id: item.id,
      number: startPage,
      window_size: internalState.remoteWindowSize,
      fields: pageFields,
    },
    {
      enabled: !!!initialData,
      onSuccess(data) {
        internalState.setPages(data.data.items as ReaderData[]);
        setPageCount(data.data.count);
      },
    }
  );

  // page number label
  useEffect(() => {
    setCountLabelVisible(true);
    const t = setTimeout(() => setCountLabelVisible(false), 4000);
    return () => clearTimeout(t);
  }, [pageNumber, pageCount]);

  // on page number change
  useEffect(() => {
    if (internalState.pages.length && internalState.pageWindow.length) {
      const p = toJS(internalState.currentPage);
      setPage(p);
      onPage?.(p);
    }
  }, [pageNumber, internalState]);

  // reset page number when page count changes
  useUpdateEffectAction(() => {
    setPageNumber(1);
    internalState.updateLocalWindow(1);
  }, [pageCount]);

  // TODO: move this to internal state
  // resets pages when image size or item changes
  useUpdateEffect(
    action(() => {
      internalState.setPages([]);
      internalState.setPageWindow([]);
    }),
    [scaling, item, internalState]
  );

  // reset page number and current page when item changes
  useUpdateEffect(
    action(() => {
      setPageNumber(1);
      internalState.setPageFocus(0, 1);
      setIsEnd(false);
    }),
    [item, internalState]
  );

  // TODO: move this to internal state
  // // Remote window, track page focus and fetch missing pages from the server when needed
  useUpdateEffect(
    action(() => {
      internalState
        .fetchMoreRemotePages(item, pageCount, pageNumber)
        .then((r) => {
          if (r !== false) {
            setPageCount(r);
          }
        });
    }),
    [internalState.pageWindow, internalState.pageFocus]
  );

  const onFocusChild = useCallback(
    action((child) => {
      console.debug(
        'focusing child',
        child,
        'of',
        internalState.pageWindow.length,
        'pages'
      );
      const childNumber = Math.max(
        0,
        Math.min(child, internalState.pageWindow.length - 1)
      );
      internalState.setPageFocus(childNumber);

      console.debug('focus child', {
        childNumber,
        page: internalState.pageWindow[childNumber],
        window: [...internalState.pageWindow],
      });
    }),
    [internalState, canvasState]
  );

  const onImageEndReached = useCallback(() => {
    canvasState.scrollToChild(canvasState.nextChild);
  }, [canvasState]);

  const onImageStartReached = useCallback(() => {
    canvasState.scrollToChild(canvasState.previousChild);
  }, [canvasState]);

  useEffect(() => {
    console.debug('page window', [...internalState.pageWindow]);
  }, [internalState.pageWindow, internalState.pageFocus]);

  useHijackHistory(
    isEnd,
    useCallback(() => setIsEnd(false), [])
  );

  const currentPages = internalState.pages;
  const currentWindow = internalState.pageWindow;
  const currentFocus = internalState.pageFocus;

  return (
    <Dimmer.Dimmable
      as={Segment}
      inverted
      blurring
      dimmed={isEnd}
      className={classNames(
        { 'no-padding-segment': !padded },
        'no-margins',
        'reader'
      )}
    >
      {blurryBg && (
        <div
          style={{
            backgroundImage: `url(${internalState.currentPage?.profile?.data})`,
          }}
          className="reader-blurry-canvas"
        />
      )}
      <Dimmer
        active={isEnd}
        className="fluid-dimmer"
        onClickOutside={useCallback(() => {
          setIsEnd(false);
        }, [])}
      >
        {children}
      </Dimmer>
      <Canvas
        state={canvasState}
        stateKey={stateKey}
        wheelZoom={wheelZoom}
        fit={fit}
        stretchFit={stretchFit}
        direction={direction}
        autoNavigate={autoNavigate}
        autoNavigateInterval={autoNavigateInterval}
        onAutoNavigateCounter={setAutoNavigateCounter}
        label={useMemo(
          () => (
            <>
              {countLabelVisible && (
                <Label size="big" className="translucent-black">
                  {pageNumber}/{pageCount}
                </Label>
              )}
            </>
          ),
          [pageNumber, pageCount, countLabelVisible]
        )}
        focusChild={currentFocus}
        onFocusChild={onFocusChild}
        onEndReached={useCallback(() => {
          if (!internalState.fetchingMore.fetching) {
            // is probably fetching more pages, don't end yet
            if (pageCount && !currentWindow.length) {
              return;
            }
            setIsEnd(true);
          }
        }, [pageCount, currentWindow])}
      >
        {currentWindow.map((i, idx) => (
          <CanvasImage
            key={`${currentPages[i].id}-${stretchFit}`}
            data-href={currentPages[i]?.profile?.data}
            href={currentPages[i]?.profile?.data}
            onError={internalState.removePageImage.bind(
              internalState,
              currentPages[i].id
            )}
            onStartReached={onImageStartReached}
            onEndReached={onImageEndReached}
            autoNavigate={autoNavigate}
            autoScroll={autoScroll}
            autoScrollSpeed={autoScrollSpeed}
            focused={idx === currentFocus}
            state={canvasState}
          />
        ))}
      </Canvas>
    </Dimmer.Dimmable>
  );
});

export default Reader;
