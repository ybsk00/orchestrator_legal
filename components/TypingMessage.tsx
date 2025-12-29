"use client";

import { useState, useEffect, useRef } from "react";

interface TypingMessageProps {
    text: string;
    speed?: number; // ms per character
    onComplete?: () => void;
}

export default function TypingMessage({ text, speed = 20, onComplete }: TypingMessageProps) {
    const [displayedText, setDisplayedText] = useState("");
    const indexRef = useRef(0);

    useEffect(() => {
        // 텍스트가 변경되면 초기화 (새 메시지 또는 수정된 메시지)
        if (text.startsWith(displayedText) && displayedText !== "") {
            // 이미 표시된 텍스트의 뒷부분만 추가된 경우 (스트리밍 등)
            // 그대로 둠
        } else {
            // 완전히 새로운 텍스트거나 다른 경우
            setDisplayedText("");
            indexRef.current = 0;
        }
    }, [text]);

    useEffect(() => {
        if (indexRef.current >= text.length) {
            if (onComplete) onComplete();
            return;
        }

        const intervalId = setInterval(() => {
            setDisplayedText((prev) => {
                const nextIndex = indexRef.current + 1;
                if (nextIndex > text.length) {
                    clearInterval(intervalId);
                    if (onComplete) onComplete();
                    return prev;
                }
                indexRef.current = nextIndex;
                return text.slice(0, nextIndex);
            });
        }, speed);

        return () => clearInterval(intervalId);
    }, [text, speed, onComplete]);

    // 줄바꿈 처리를 위해 whitespace-pre-wrap 사용
    return <div className="whitespace-pre-wrap">{displayedText}</div>;
}
