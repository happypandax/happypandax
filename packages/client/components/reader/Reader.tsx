import classNames from 'classnames';
import _ from 'lodash';
import { makeAutoObservable, toJS } from 'mobx';
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
import { FieldPath, ReaderData, ServerPage } from '../../shared/types';
import {
  ReaderState,
  useInitialRecoilState,
  useInitialRecoilValue,
} from '../../state';
import Canvas, { CanvasState } from './Canvas';
import CanvasImage from './CanvasImage';

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


  lastReadPageId: number = 0;

  pageFocus: number = 0;
  // indexes of pages that are currently active
  pageWindow: number[] = [];
  pages: ReaderData[] = [];

  // Two layers of "windows", one for the actual pages fetched from the server (remote), another for the active pages to be loaded (images) for the client (local)
  // When the local window runs out of pages, the remote window readjusts and fetches more pages if needed

  windowSize: number = 10;
  remoteWindowSize: number = 40;

  fetchingMore = {
    fetching: false,
    previousNumber: 1,
  };
  fetchingImages: number[] = [];
  retryImages: { [k: number]: number } = {};

  // keep track of image refetch retries
  maxRetries = 3;

  private _disposers: Array<() => void>;

  constructor() {

    this._disposers = [];

    makeAutoObservable(this);
  }

  get currentPage() {
    return this.pages?.[this.pageWindow?.[this.pageFocus]]
  }

  setWindowSize(size: number, pageCount?: number) {
    this.windowSize = Math.min(size, this.pages.length || (pageCount ?? 1));
  }

  setRemoteWindowSize(size: number, pageCount?: number) {
    this.remoteWindowSize = Math.max(40, size ?? Math.ceil(this.windowSize * 2))
  }

  fetchImages(scaling: 0 | ImageSize) {


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
        .filter((p) => !p?.profile?.data)
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
        if (scaling !== undefined) {
          size = scaling === 0 ? getOptimalImageSize() : scaling;
        }

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
            this.pages = update(this.pages, spec)
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
    this.pages = update(this.pages, { [pageIndex]: { profile: { $set: undefined } } })
  }

  dispose() {
    this._disposers.forEach((d) => d());
  }
}

const Reader = observer(function Reader({
  initialData,
  pageCount: initialPageCount = 0,
  windowSize: initialWindowSize = 10,
  remoteWindowSize: initialRemoteWindowSize,
  startPage = 1,
  onPage,
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
  fit?: ItemFit;
  stretchFit?: boolean;
  blurryBg?: boolean;
  autoNavigate?: boolean;
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
  const autoNavigate = useInitialRecoilValue(
    ReaderState.autoNavigate(stateKey),
    initialAutoNavigate
  );
  const autoNavigateInterval = useInitialRecoilValue(
    ReaderState.autoNavigateInterval(stateKey),
    initialAutoNavigateInterval
  );
  const direction = useInitialRecoilValue(
    ReaderState.direction(stateKey),
    initialDirection
  );

  const fit = useInitialRecoilValue(
    ReaderState.fit(stateKey),
    initialFit
  );

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
    return new InternalReaderState();
  }, []);

  useUnmount(() => {
    internalState.dispose();
  });


  const canvasState = useMemo(() => {
    return new CanvasState();
  }, []);

  useUnmount(() => canvasState.dispose());


  useEffect(() => {
    internalState.pages = initialData
  }, [initialData, internalState])


  useEffect(() => {
    internalState.setWindowSize(initialWindowSize, pageCount)
  }, [initialWindowSize, pageCount, internalState])

  useEffect(() => {
    internalState.setRemoteWindowSize(initialRemoteWindowSize, pageCount)
  }, [initialRemoteWindowSize, internalState])

  useEffect(() => {
    setPageCount(initialPageCount);
  }, [initialPageCount]);




  const [countLabelVisible, setCountLabelVisible] = useState(false);

  // keep track of image refetch retries

  const maxRetries = 3;


  // page change

  useEffect(() => {
    const lastpage = internalState.currentPage;
    if (lastpage) {
      return () => {
        if (internalState.lastReadPageId !== lastpage.id) {
          pageReadEvent({ item_id: lastpage.id });
          internalState.lastReadPageId = lastpage.id;
        }
      };
    }
  }, [internalState.currentPage]);

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
      enabled: !!!initialData, onSuccess(data) {
        internalState.pages = data.data.items as ReaderData[];
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
      // there should be no issue with the page being wrong here
      const p = toJS(internalState.currentPage);
      setPage(p);
      onPage?.(p);
    }
  }, [pageNumber, internalState]);

  // reset page number when page count changes
  useEffect(() => {
    setPageNumber(1);
  }, [pageCount]);


  // reset pages when image size or item changes
  useUpdateEffect(() => {
    internalState.pages = [];
    internalState.pageWindow = [];
  }, [scaling, item, internalState]);

  // reset page number and current page when item changes
  useUpdateEffect(() => {
    setPageNumber(1);
    internalState.pageFocus = 0;
    setIsEnd(false);
  }, [item, internalState]);


  // // Remote window, track page focus and fetch missing pages from the server when needed
  useUpdateEffect(() => {
    if (isNaN(internalState.pageFocus)) {
      return;
    }

    let fetchMore: 'left' | 'right' = undefined;

    if (internalState.pageWindow.length) {
      // how close to the edge of the local window needed to be before more pages should be fetched
      const offset = Math.min(Math.floor(internalState.windowSize / 2), 3);

      const leftPageFocusOffset = Math.max(internalState.pageFocus - offset, 0);
      const rightPageFocusOffset = Math.min(
        internalState.pageFocus + offset,
        internalState.pageWindow.length - 1
      );

      // when close to the left side and the page on the left side is not the first, fetch more
      if (
        internalState.pageWindow[leftPageFocusOffset] === 0 &&
        internalState.pages[internalState.pageWindow[leftPageFocusOffset]].number !== 1
      ) {
        fetchMore = 'left';
      }
      // when close to the right side and the page on the right side is not the last, fetch more
      else if (
        internalState.pageWindow[rightPageFocusOffset] === internalState.pages.length - 1 &&
        internalState.pages[internalState.pageWindow[rightPageFocusOffset]].number !== pageCount
      ) {
        fetchMore = 'right';
      }
    } else if (internalState.pages.length || pageCount) {
      fetchMore = 'left';
    }

    console.debug('pages', internalState.pages)
    console.debug('pageWindow', internalState.pageWindow)
    console.debug('pageFocus', internalState.pageFocus)

    const pNumber = internalState.pageWindow.length
      ? internalState.currentPage.number
      : pageNumber;

    if (
      fetchMore &&
      !internalState.fetchingMore.fetching &&
      (!internalState.pages.length || internalState.fetchingMore.previousNumber !== pNumber)
    ) {
      // when the focus gets corrected by the local window, this hook will retrigger so we need to make sure we don't refetch
      internalState.fetchingMore.previousNumber = pNumber;

      internalState.fetchingMore.fetching = true;
      Query.fetch(QueryType.PAGES, {
        gallery_id: item.id,
        number: pNumber,
        fields: pageFields,
        window_size: internalState.remoteWindowSize,
      })
        .then((r) => {
          // required, or pageWindow hook won't see it in time
          internalState.fetchingMore.fetching = false;
          internalState.pages = r.data.items as ReaderData[];
          setPageCount(r.data.count);
        })
        .finally(() => {
          // in case of error
          internalState.fetchingMore.fetching = false;
        });
    }
  }, [internalState.pageWindow, internalState.pageFocus]);

  // Local window, set window of active local pages based on page number
  useEffect(() => {
    if (internalState.fetchingMore.fetching) {
      return;
    }

    const idx = Math.max(
      0,
      internalState.pages.findIndex((p) => p.number === pageNumber)
    );

    const windowed = windowedPages(
      idx,
      internalState.windowSize,
      Math.max(internalState.pages.length - 1, 0)
    );

    // correct focus, this is after more pages have been fetched, then the focus may point at the wrong page
    windowed.forEach((n, i) => {
      if (internalState.pages[n].number === pageNumber && i !== internalState.pageFocus) {
        internalState.pageFocus = i;
      }
    });

    if (!_.isEqual(internalState.pageWindow, windowed)) {
      internalState.pageWindow = windowed;
    }
  }, [internalState.windowSize, pageNumber, internalState.pages, internalState.pageWindow]);


  // fetch missing images for windowed pages

  useEffect(() => {
    if (!internalState.fetchingImages) {
      internalState.fetchingImages = [];
    }

    internalState.fetchImages(scaling);
  }, [scaling, internalState]);

  const onFocusChild = useCallback(
    (child) => {
      const childNumber = Math.max(0, Math.min(child, internalState.pageWindow.length - 1));
      console.log("page focus", childNumber)
      internalState.pageFocus = childNumber;

      // make sure page number is in sync
      if (internalState.pages.length && internalState.pageWindow.length) {
        const page = internalState.pages[internalState.pageWindow[childNumber]];
        if (page.number !== pageNumber) {
          setPageNumber(page.number);
        }
      } else {
        setPageNumber(0);
      }
    },
    [internalState.pageWindow, internalState.pages]
  );

  return (
    <Dimmer.Dimmable
      as={Segment}
      inverted
      blurring
      dimmed={isEnd}
      className={classNames({ 'no-padding-segment': !padded }, 'no-margins')}>
      {blurryBg && (
        <div
          style={{
            backgroundImage: `url(${internalState.currentPage?.profile?.data
              })`,
          }}
          className="reader-blurry-canvas"
        />
      )}
      <Dimmer
        active={isEnd}
        className="fluid-dimmer"
        onClickOutside={useCallback(() => {
          setIsEnd(false);
        }, [])}>
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
        focusChild={internalState.pageFocus}
        onFocusChild={onFocusChild}
        onEnd={useCallback(() => {
          if (!internalState.fetchingMore.fetching) {
            // is probably fetching more pages, don't end yet
            if (pageCount && !internalState.pageWindow.length) {
              return;
            }
            setIsEnd(true);
          }
        }, [pageCount, internalState.pageWindow])}>
        {internalState.pageWindow.map((i, idx) => (
          <CanvasImage
            key={`${internalState.pages[i].id}-${stretchFit}`}
            href={PLACEHOLDERS[i].url} //{pages[i]?.profile?.data}
            onError={internalState.removePageImage.bind(internalState, internalState.pages[i].id)}
            focused={idx === internalState.pageFocus}
            state={canvasState}
          />
        ))}
      </Canvas>
    </Dimmer.Dimmable>
  );
}
);

export default Reader;
