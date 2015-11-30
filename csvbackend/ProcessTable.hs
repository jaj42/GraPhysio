module ProcessTable where

import Util(subsetList, every)

import qualified Data.ByteString.Lazy.Char8 as C
import           Data.List
import           Data.Maybe
import           Text.CSV.Lazy.ByteString

data Range     = All
               | Subset Int Int
  deriving (Read,Show)

data Command   = ErrSyntax
               | CloseConnection
               | ReadVector { fileName  :: String
                            , seperator :: Char
                            , fields    :: [String]
                            , range     :: Range
                            , notnull   :: [String]
                            , skiplines :: Int }
  deriving (Read,Show)
 
-- | Process: first select fields, then filter header, then filter null, then subset, then skip lines
processCsv :: Command -> IO CSVTable
processCsv c = do
  csvcontent <- C.readFile (fileName c)
  let csvresult = parseDSV False (seperator c) csvcontent
  let notnullpos = getElemPos c
  rows <- case selectFields (fields c) (csvTableFull csvresult) of
               Left   _        -> return $ take 1 $ mkEmptyColumn "MissingField"
               Right selection -> return selection
  let rowsNoHeader = drop 1 rows
  let rFiltered = filter (areFieldsNull notnullpos) rowsNoHeader
  let rSubset   = case (range c) of
       All               -> rFiltered
       Subset start stop -> subsetList (start,stop) rFiltered
  return (every (skiplines c) rSubset)

-- | Gets the positions of the fields that cannot be null.
getElemPos :: Command -> [Int]
getElemPos c = fromJust `fmap` map (`elemIndex` headers) notnullfields
  where
    headers = fields c
    notnullfields = notnull c

-- | Tests if any of the given fields are null.
areFieldsNull :: [Int] -> [CSVField] -> Bool
areFieldsNull indexes csvfields = and nullfields
  where
    subsetfields = map (csvfields !!) indexes
    fieldscontent = map csvFieldContent subsetfields
    nullfields = map (not.(C.null)) fieldscontent
