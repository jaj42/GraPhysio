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
 
processCsv :: Command -> IO CSVTable
processCsv c = do
  csvcontent <- C.readFile (fileName c)
  let csvresult = parseDSV False (seperator c) csvcontent
  let notnullpos = getElemPos c
  fieldlist <- case selectFields (fields c) (csvTableFull csvresult) of
                    Left   _        -> return $ take 1 $ mkEmptyColumn "MissingField"
                    Right selection -> return selection
  let fieldlistNoHeader = drop 1 fieldlist
  let resulttmp = case (range c) of
       All               -> fieldlistNoHeader
       Subset start stop -> subsetList (start,stop) fieldlistNoHeader
  let result = filter (areFieldsNull notnullpos) resulttmp
  return (every (skiplines c) result)

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
