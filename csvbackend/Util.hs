{-# LANGUAGE OverloadedStrings #-}
module Util where

import Text.CSV.Lazy.ByteString
import qualified Data.ByteString.Lazy.Char8 as C
import Data.ByteString.Lazy.Search as BS
import Data.ByteString.Builder.Extra
import Data.ByteString.Builder
import Data.Monoid

-- Borrowed from Control.Monad.Loops (Public Domain)
whileM_ :: (Monad m) => m Bool -> m a -> m ()
whileM_ p f = go
    where go = do
            x <- p
            if x
                then f >> go
                else return ()

-- Strangely this is not in the standard library
subsetList :: (Int,Int) -> [a] -> [a]
subsetList (start,stop) l = take (stop - start + 1) (drop (start - 1) l)

every :: Int -> [a] -> [a]
every n (x:xs) = x : every n (drop (n - 1) xs)
every _ []     = []

--instance MessagePack CSVField where
--    toObject f@(CSVField{})   = toObject (csvFieldContent f)
--    toObject CSVFieldError{}  = ObjectNil
--    fromObject o = case o of
--        ObjectBin f -> Just $ mkCSVField 0 0 (C.fromStrict f)
--        _           -> Nothing
--
--instance ToJSON CSVField where
--    toJSON f@(CSVField{})     = toJSON $ C.unpack (csvFieldContent f)
--    toEncoding f@(CSVField{}) = toEncoding $ C.unpack (csvFieldContent f)

class ToSerial a where 
    toSerial :: a -> Builder

-- Very simple home-made JSON serializer
instance ToSerial CSVField where
    toSerial f = toSerial $ correctfloat (csvFieldContent f)
      where
        correctfloat = BS.replace "," (BS.strictify ".")

instance ToSerial C.ByteString where
    toSerial s = char7 '"' <> (lazyByteString s) <> char7 '"'

instance (ToSerial a) => ToSerial [a] where
    toSerial l  = char7 '[' <> (toSerialSub l) <> char7 ']'
      where
        toSerialSub []     = mempty
        toSerialSub (c:cs) = toSerial c <> mconcat [ char7 ',' <> toSerial c' | c' <- cs ]

serialize :: ToSerial a => a -> C.ByteString
serialize = myToLazyByteString . toSerial
  where myToLazyByteString = toLazyByteStringWith (untrimmedStrategy smallChunkSize defaultChunkSize) "\n"
