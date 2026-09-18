import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ReallocationModal } from '../reallocation/ReallocationModal';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isReallocationModalOpen, setIsReallocationModalOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#f6f8fa]">
      <Sidebar onOpenReallocationModal={() => setIsReallocationModalOpen(true)} />
      
      <div className="flex-1 flex flex-col min-w-0">
        <Header onOpenReallocationModal={() => setIsReallocationModalOpen(true)} />
        
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          {children}
        </main>
      </div>

      <ReallocationModal
        isOpen={isReallocationModalOpen}
        onClose={() => setIsReallocationModalOpen(false)}
      />
    </div>
  );
};
