import { Dimmer, Portal, Segment, Sidebar } from 'semantic-ui-react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import MainSidebar from '../Sidebar';
import { ScrollUpButton, Visible } from '../Misc';
import classNames from 'classnames';
import {
  FilterButtonInput,
  SortButtonInput,
  OnlyFavoritesButton,
  ClearFilterButton,
} from './ItemLayout';

export function BottomZoneItem({
  children,
  x,
  y,
  className,
}: {
  className?: string;
  children?: React.ReactNode;
  x: 'left' | 'right';
  y: 'top' | 'bottom';
}) {
  return <div className={classNames('item', x, y, className)}>{children}</div>;
}

export function BottomZone({ children }: { children?: React.ReactNode }) {
  return (
    <Portal open>
      <div id="bottom_zone">
        <div>{children}</div>
      </div>
    </Portal>
  );
}

export default function PageLayout({
  dimmed,
  menu,
  children,
}: {
  dimmed?: boolean;
  menu?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <>
      <MainSidebar />
      {menu}
      <Sidebar.Pusher
        as={Dimmer.Dimmable}
        dimmed={dimmed}
        className="force-viewport-size">
        <Dimmer simple active={dimmed} />
        <DndProvider backend={HTML5Backend}>
          {children}
          <BottomZone>
            <BottomZoneItem x="right" y="top" className="flex fullheight">
              <OnlyFavoritesButton />
              <div className="medium-margin-top">
                <div className="pos-relative">
                  <FilterButtonInput />
                  <Visible visible>
                    <ClearFilterButton className="clear_filter" size="mini" />
                  </Visible>
                </div>
              </div>
              <div className="medium-margin-top mb-auto">
                <SortButtonInput />
              </div>
              <ScrollUpButton />
            </BottomZoneItem>
          </BottomZone>
        </DndProvider>
      </Sidebar.Pusher>
    </>
  );
}
