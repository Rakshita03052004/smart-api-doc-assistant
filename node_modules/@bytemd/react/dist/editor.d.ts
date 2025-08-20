import * as bytemd from 'bytemd';
import React from 'react';
export interface EditorProps extends bytemd.EditorProps {
    onChange?(value: string): void;
}
export declare const Editor: React.FC<EditorProps>;
